import os
import sys
from pathlib import Path
from typing import Tuple

import click
import rich
from rich.progress import Progress
from rich.syntax import Syntax

from betterproto.plugin.cli import (
    DEFAULT_LINE_LENGTH,
    DEFAULT_OUT,
    ENV,
    USE_PROTOC,
    VERBOSE,
    utils,
)

from ..models import monkey_patch_oneof_index
from .errors import CLIError, ProtobufSyntaxError
from .runner import compile_protobufs

monkey_patch_oneof_index()


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.pass_context
def main(ctx: click.Context) -> None:
    """The main entry point to all things betterproto"""
    if ctx.invoked_subcommand is None:
        rich.print(ctx.get_help())


@main.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    default=VERBOSE,
)
@click.option(
    "-p",
    "--protoc",
    is_flag=True,
    help="Whether or not to use protoc to compile the protobufs if this is false"
    "it will attempt to use grpc instead",
    default=USE_PROTOC,
)
@click.option(
    "-l",
    "--line-length",
    type=int,
    default=DEFAULT_LINE_LENGTH,
)
@click.option(
    "--generate-services",
    help="Whether or not to generate servicer stubs",
    is_flag=True,
    default=True,
)
@click.option(
    "-o",
    "--output",
    help="The output directory",
    type=click.Path(file_okay=False, dir_okay=True, allow_dash=True),
    default=DEFAULT_OUT.name,
)
@click.argument(
    "src",
    type=click.Path(exists=True, file_okay=True, dir_okay=True, allow_dash=True),
    is_eager=True,
    nargs=-1,
)
@utils.run_sync
async def compile(
    verbose: bool,
    protoc: bool,
    line_length: int,
    generate_services: bool,
    output: str,
    src: Tuple[str, ...],
) -> None:
    """The recommended way to compile your protobuf files."""
    if len(src) != 1:
        return rich.print(
            "[red]Currently can't handle more than one source this is just for a "
            "nicer invocation of help"
        )

    files = utils.get_files(src[0])
    if not files:
        return rich.print("[bold]No files found to compile")

    output = Path.cwd() / output
    output.mkdir(exist_ok=True)

    ENV["USING_BETTERPROTO_CLI"] = "true"

    try:
        await compile_protobufs(
            *files,
            output=output,
            verbose=verbose,
            use_protoc=protoc,
            generate_services=generate_services,
            line_length=line_length,
        )
    except ProtobufSyntaxError as exc:
        error = Syntax(
            exc.file.read_text(),
            lexer_name="proto",
            line_numbers=True,
            line_range=(max(exc.lineno - 5, 0), exc.lineno),
        )
        # I'd like to switch to .from_path but it appears to be bugged and doesnt pick up syntax
        return rich.print(
            f"[red]File {str(exc.file).strip()}:\n",
            error,
            f"[red]{' ' * (exc.offset + 3)}^\n"
            f"[red]SyntaxError: {exc.msg}",
        )
    except CLIError as exc:
        failed_files = "\n".join(f" - {file}" for file in files)
        return rich.print(
            f"[red]{'Protoc' if protoc else 'GRPC'} failed to generate outputs for:\n\n"
            f"{failed_files}\n\nSee the output for the issue:\n{exc.args[0]}[red]",
        )

    rich.print(
        f"[bold]Finished generating output for {len(files)} files, output is in [link]{output.as_posix()}"
    )


"""
async def run_cli(port: int) -> None:

    with Progress(transient=True) as progress:  # TODO reading and compiling stuff
        compiling_progress_bar = progress.add_task(
            "[green]Compiling protobufs...", total=total
        )

        async for message in service.get_currently_compiling():
            progress.tasks[0].description = (
                f"[green]Compiling protobufs...\n"
                f"Currently compiling {message.type.name.lower()}: {message.name}"
            )
            progress.update(compiling_progress_bar, advance=1)
    rich.print(f"[bold][green]Finished compiling output should be at {round(3)}")"""

if __name__ == "__main__":
    os.getcwd = lambda: "/Users/gobot1234/PycharmProjects/betterproto/tests"
    sys.argv = "betterproto compile /Users/gobot1234/PycharmProjects/betterproto/tests/inputs/bool".split()
    main()
