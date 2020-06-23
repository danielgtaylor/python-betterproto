#!/usr/bin/env python
import glob
import os
import shutil
import subprocess
import sys
from typing import Set

from betterproto.tests.util import (
    get_directories,
    inputs_path,
    output_path_betterproto,
    output_path_reference,
    protoc_plugin,
    protoc_reference,
)

# Force pure-python implementation instead of C++, otherwise imports
# break things because we can't properly reset the symbol database.
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"


def clear_directory(path: str):
    for file_or_directory in glob.glob(os.path.join(path, "*")):
        if os.path.isdir(file_or_directory):
            shutil.rmtree(file_or_directory)
        else:
            os.remove(file_or_directory)


def generate(whitelist: Set[str]):
    path_whitelist = {os.path.realpath(e) for e in whitelist if os.path.exists(e)}
    name_whitelist = {e for e in whitelist if not os.path.exists(e)}

    test_case_names = set(get_directories(inputs_path))

    failed_test_cases = []

    for test_case_name in sorted(test_case_names):
        test_case_input_path = os.path.realpath(
            os.path.join(inputs_path, test_case_name)
        )

        if (
            whitelist
            and test_case_input_path not in path_whitelist
            and test_case_name not in name_whitelist
        ):
            continue

        print(f"Generating output for {test_case_name}")
        try:
            generate_test_case_output(test_case_name, test_case_input_path)
        except subprocess.CalledProcessError as e:
            failed_test_cases.append(test_case_name)

    if failed_test_cases:
        sys.stderr.write("\nFailed to generate the following test cases:\n")
        for failed_test_case in failed_test_cases:
            sys.stderr.write(f"- {failed_test_case}\n")


def generate_test_case_output(test_case_name, test_case_input_path=None):
    if not test_case_input_path:
        test_case_input_path = os.path.realpath(
            os.path.join(inputs_path, test_case_name)
        )

    test_case_output_path_reference = os.path.join(
        output_path_reference, test_case_name
    )
    test_case_output_path_betterproto = os.path.join(
        output_path_betterproto, test_case_name
    )

    os.makedirs(test_case_output_path_reference, exist_ok=True)
    os.makedirs(test_case_output_path_betterproto, exist_ok=True)

    clear_directory(test_case_output_path_reference)
    clear_directory(test_case_output_path_betterproto)

    protoc_reference(test_case_input_path, test_case_output_path_reference)
    protoc_plugin(test_case_input_path, test_case_output_path_betterproto)


HELP = "\n".join(
    [
        "Usage: python generate.py",
        "       python generate.py [DIRECTORIES or NAMES]",
        "Generate python classes for standard tests.",
        "",
        "DIRECTORIES    One or more relative or absolute directories of test-cases to generate classes for.",
        "               python generate.py inputs/bool inputs/double inputs/enum",
        "",
        "NAMES          One or more test-case names to generate classes for.",
        "               python generate.py bool double enums",
    ]
)


def main():
    if set(sys.argv).intersection({"-h", "--help"}):
        print(HELP)
        return
    whitelist = set(sys.argv[1:])

    generate(whitelist)


if __name__ == "__main__":
    main()
