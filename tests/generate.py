#!/usr/bin/env python
import asyncio
import os
import shutil
import sys
from pathlib import Path
from typing import Optional, Set, List

import typer
import rich

from betterproto.plugin.cli import compile_protobufs, utils
from tests.util import (
    get_directories,
    inputs_path,
    output_path_betterproto,
    output_path_reference,
)

# Force pure-python implementation instead of C++, otherwise imports
# break things because we can't properly reset the symbol database.
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
app = typer.Typer()


def clear_directory(dir_path: Path) -> None:
    for file_or_directory in dir_path.glob("*"):
        if file_or_directory.is_dir():
            shutil.rmtree(file_or_directory)
        else:
            file_or_directory.unlink()


async def generate(whitelist: Set[Path], verbose: bool) -> None:
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
        test_case_input_path = (inputs_path / test_case_name).resolve()
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
    # Wait for processes before match any failures to names to report
    for test_case_name, exception in zip(
        sorted(test_case_names), await asyncio.gather(*generation_tasks)
    ):
        if exception is not None:
            failed_test_cases.append(test_case_name)

    if failed_test_cases:
        rich.print(
            "[red bold]\nFailed to generate the following test cases:",
            *(f"[red]- {failed_test_case}" for failed_test_case in failed_test_cases),
            sep="\n",
        )


async def generate_test_case_output(
    test_case_input_path: Path, test_case_name: str, verbose: bool
) -> Optional[Exception]:
    """
    Returns the max of the subprocess return values
    """

    test_case_output_path_reference = output_path_reference / test_case_name
    test_case_output_path_betterproto = output_path_betterproto / test_case_name

    os.makedirs(test_case_output_path_reference, exist_ok=True)
    os.makedirs(test_case_output_path_betterproto, exist_ok=True)

    clear_directory(test_case_output_path_reference)
    clear_directory(test_case_output_path_betterproto)

    files = list(test_case_input_path.glob("*.proto"))
    ref_errs, plg_errs = await asyncio.gather(
        compile_protobufs(
            *files, output=test_case_output_path_reference, use_betterproto=False
        ),
        compile_protobufs(
            *files, output=test_case_output_path_betterproto, from_cli=True
        ),
    )

    rich.print(f"[bold red]Generated output for {test_case_name!r}")
    if verbose:
        for ref_err in ref_errs:
            rich.print(f"[red]{ref_err}", file=sys.stderr)
        for plg_err in plg_errs:
            rich.print(f"[red]{plg_err}", file=sys.stderr)
        sys.stderr.flush()

    return ref_errs or plg_errs or None


@app.command(context_settings={"help_option_names": ["-h", "--help"]})
@utils.run_sync
async def main(
    verbose: bool = typer.Option(
        False,
        "-v",
        "--verbose",
        help="Whether or not to run the plugin in verbose mode.",
    ),
    directories: Optional[List[Path]] = typer.Argument(
        None,
        help="One or more relative or absolute directories or test-case names "
        "test-cases to generate classes for. e.g. ``inputs/bool inputs/double "
        "inputs/enum`` or ``bool double enum``",
    ),
) -> None:
    """Generate python classes for standard tests."""
    await generate(set(directories or ()), verbose)


if __name__ == "__main__":
    app()
