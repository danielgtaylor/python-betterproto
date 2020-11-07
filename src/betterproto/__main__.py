import subprocess
import sys
from functools import partial
from pathlib import Path
from typing import Tuple

import black
import click

DEFAULT_OUT = Path.cwd() / "betterproto_out"
VERBOSE = False
try:
    import grpc
except ImportError:
    USE_PROTOC = True
else:
    USE_PROTOC = False


out = partial(click.secho, bold=True, err=True)
err = partial(click.secho, fg="red", err=True)


def recursive_file_finder(directory: Path) -> Tuple[Path, ...]:
    files = set()
    for path in directory.iterdir():
        if path.is_file() and path.name.endswith(".proto"):
            files.add(path)
        elif path.is_dir():
            files.update(recursive_file_finder(path))

    return tuple(files)


def compile_files(*files: Path, output_dir: Path) -> None:
    files = [file.as_posix() for file in files]
    command = [
        f"--python_betterproto_out={output_dir.as_posix()}",
        "-I",
        output_dir.parent.as_posix(),
        *files,
    ]
    if USE_PROTOC:
        command.insert(0, "protoc")
    else:
        command.insert(0, "grpc.tools.protoc")
        command.insert(0, "-m")
        command.insert(0, sys.executable)

    proc = subprocess.Popen(
        args=command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    stdout, stderr = proc.communicate()
    stdout = stdout.decode()
    stderr = stderr.decode()

    if proc.returncode != 0:
        failed_files = "\n".join(f" - {file}" for file in files)
        return err(
            f"{'Protoc' if USE_PROTOC else 'GRPC'} failed to generate outputs for:\n\n"
            f"{failed_files}\n\nSee the output for the issue:\n{stderr}"
        )

    if VERBOSE:
        out(f"VERBOSE: {stdout}")

    out(
        f"Finished generating output for {len(files)} files, compiled output should be "
        f"in {output_dir.as_posix()}"
    )


@click.group()
@click.pass_context
def main(ctx: click.Context):
    """The main entry point to all things betterproto"""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@main.command()
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
)
@click.option(
    "-p",
    "--protoc",
    is_flag=True,
    help="Whether or not to use protoc or GRPC to compile the protobufs",
    default=USE_PROTOC,
)
@click.option(
    "-o",
    "--output",
    help="The output directory",
    default=DEFAULT_OUT.name,
    is_eager=True,
)
@click.argument(
    "src",
    type=click.Path(
        exists=True, file_okay=True, dir_okay=True, readable=True, allow_dash=True
    ),
    is_eager=True,
)
def compile(verbose: bool, protoc: bool, output: str, src: str):
    """The recommended way to compile your protobuf files."""
    directory = Path.cwd().joinpath(src)
    files = recursive_file_finder(directory) if directory.is_dir() else (directory,)
    if not files:
        return out("No files found to compile")

    output = Path.cwd().joinpath(output)
    output.mkdir(exist_ok=True)

    # Update constants/flags
    globs = globals()
    globs["VERBOSE"] = verbose

    return compile_files(*files, output_dir=output)


# Decorators aren't handled very well
main: click.Group
compile: click.Command


if __name__ == "__main__":
    black.patch_click()
    main()
