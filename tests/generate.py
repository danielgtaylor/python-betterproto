#!/usr/bin/env python
import asyncio
import os
import platform
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Set

from tests.util import (
    GetProtocArgs,
    get_directories,
    inputs_path,
    output_path_betterproto,
    output_path_betterproto_pydantic,
    output_path_betterproto_twirp,
    output_path_reference,
    protoc,
)


# Force pure-python implementation instead of C++, otherwise imports
# break things because we can't properly reset the symbol database.
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"


@dataclass
class OutputConfig:
    label: str
    output_path: str
    protoc_args: GetProtocArgs


def print_success(message: str):
    print(f"\033[32;1;4m{message}\033[0m")


def print_error(message: str):
    print(f"\033[31;1;4m{message}\033[0m")


def clear_directory(dir_path: Path):
    for file_or_directory in dir_path.glob("*"):
        if file_or_directory.is_dir():
            shutil.rmtree(file_or_directory)
        else:
            file_or_directory.unlink()


async def generate(whitelist: Set[str], verbose: bool):
    test_case_names = set(get_directories(inputs_path)) - {"__pycache__"}

    path_whitelist = set()
    name_whitelist = set()
    for item in whitelist:
        if item in test_case_names:
            name_whitelist.add(item)
            continue
        path_whitelist.add(item)

    generation_tasks = []
    for test_case_name in sorted(test_case_names):
        test_case_input_path = inputs_path.joinpath(test_case_name).resolve()
        if (
            whitelist
            and str(test_case_input_path) not in path_whitelist
            and test_case_name not in name_whitelist
        ):
            continue
        generation_tasks.append(
            generate_test_case_output(test_case_input_path, test_case_name, verbose)
        )

    failed_test_cases = []
    # Wait for all subprocs and match any failures to names to report
    for test_case_name, result in zip(
        sorted(test_case_names), await asyncio.gather(*generation_tasks)
    ):
        if result != 0:
            failed_test_cases.append(test_case_name)

    if len(failed_test_cases) > 0:
        sys.stderr.write(
            "\n\033[31;1;4mFailed to generate the following test cases:\033[0m\n"
        )
        for failed_test_case in failed_test_cases:
            sys.stderr.write(f"- {failed_test_case}\n")

        sys.exit(1)


async def generate_test_case_output(
    test_case_input_path: Path, test_case_name: str, verbose: bool
) -> int:
    """
    Returns the max of the subprocess return values
    """

    output_configs = [
        OutputConfig(
            label='reference output',
            output_path=output_path_reference.joinpath(test_case_name),
            protoc_args=lambda output_dir: [
                f"--python_out={output_dir}",
            ],
        ),
        OutputConfig(
            label='plugin output',
            output_path=output_path_betterproto,
            protoc_args=lambda output_dir: [
                f"--python_betterproto_out={output_dir}",
            ],
        ),
        OutputConfig(
            label='plugin (pydantic compatible)',
            output_path=output_path_betterproto_pydantic,
            protoc_args=lambda output_dir: [
                "--experimental_allow_proto3_optional",
                f"--python_betterproto_out={output_dir}",
                "--python_betterproto_opt=pydantic_dataclasses",
            ],
        ),
        OutputConfig(
            label='plugin (twirp service impl)',
            output_path=output_path_betterproto_twirp,
            protoc_args=lambda output_dir: [
                f"--python_betterproto_out={output_dir}",
                "--python_betterproto_opt=service_impl=twirp",
            ],
        ),
    ]

    protoc_calls = []
    for config in output_configs:
        os.makedirs(config.output_path, exist_ok=True)
        clear_directory(config.output_path)
        protoc_calls.append(
            protoc(test_case_input_path, config.output_path, config.protoc_args),
        )

    results = await asyncio.gather(*protoc_calls)

    max_status = 0
    for result, config in zip(results, output_configs):
        protoc_stdout, protoc_stderr, protoc_status = result
        max_status = max(max_status, protoc_status)

        if protoc_status == 0:
            print_success(f"Generated {config.label} output for {test_case_name!r}")
        else:
            print_error(f"Failed to generate {config.label} output for {test_case_name!r}")

        if verbose:
            if protoc_stdout:
                print(f"{config.label} stdout:")
                sys.stdout.buffer.write(protoc_stdout)
                sys.stdout.buffer.flush()

            if protoc_stderr:
                print(f"{config.label} stderr:")
                sys.stderr.buffer.write(protoc_stderr)
                sys.stderr.buffer.flush()

    return max_status


HELP = "\n".join(
    (
        "Usage: python generate.py [-h] [-v] [DIRECTORIES or NAMES]",
        "Generate python classes for standard tests.",
        "",
        "DIRECTORIES    One or more relative or absolute directories of test-cases to generate classes for.",
        "               python generate.py inputs/bool inputs/double inputs/enum",
        "",
        "NAMES          One or more test-case names to generate classes for.",
        "               python generate.py bool double enums",
    )
)


def main():
    if set(sys.argv).intersection({"-h", "--help"}):
        print(HELP)
        return
    if sys.argv[1:2] == ["-v"]:
        verbose = True
        whitelist = set(sys.argv[2:])
    else:
        verbose = False
        whitelist = set(sys.argv[1:])

    if platform.system() == "Windows":
        # for python version prior to 3.8, loop policy needs to be set explicitly
        # https://docs.python.org/3/library/asyncio-policy.html#asyncio.DefaultEventLoopPolicy
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        except AttributeError:
            # python < 3.7 does not have asyncio.WindowsProactorEventLoopPolicy
            asyncio.get_event_loop_policy().set_event_loop(asyncio.ProactorEventLoop())

    try:
        asyncio.run(generate(whitelist, verbose))
    except AttributeError:
        # compatibility code for python < 3.7
        asyncio.get_event_loop().run_until_complete(generate(whitelist, verbose))


if __name__ == "__main__":
    main()
