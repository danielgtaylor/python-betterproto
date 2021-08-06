import sys
from pathlib import Path
from typing import List, Optional

from .. import install_exception_hook
install_exception_hook()

import protobuf_parser
import rich
import typer
from rich.syntax import Syntax

from ... import __version__
from ..models import monkey_patch_oneof_index
from . import DEFAULT_LINE_LENGTH, VERBOSE, utils
from .runner import compile_protobufs

monkey_patch_oneof_index()
app = typer.Typer()


@app.callback(context_settings={"help_option_names": ["-h", "--help"]})
def callback(ctx: typer.Context) -> None:
    """The callback for all things betterproto"""
    if ctx.invoked_subcommand is None:
        rich.print(ctx.get_help())


@app.command()
def version(ctx: typer.Context) -> None:
    rich.print("betterproto version:", __version__)


@app.command(context_settings={"help_option_names": ["-h", "--help"]})
@utils.run_sync
async def compile(
    verbose: bool = typer.Option(
        VERBOSE, "-v", "--verbose", help="Whether or not to be verbose"
    ),
    line_length: int = typer.Option(
        DEFAULT_LINE_LENGTH,
        "-l",
        "--line-length",
        help="The line length to format with",
    ),
    generate_services: bool = typer.Option(
        True, help="Whether or not to generate servicer stubs"
    ),
    output: Optional[Path] = typer.Option(
        None,
        help="The name of the output directory",
        file_okay=False,
        allow_dash=True,
    ),
    paths: List[Path] = typer.Argument(
        ...,
        help="The protobuf files to compile",
        exists=True,
        allow_dash=True,
        readable=False,
    ),
) -> None:
    """The recommended way to compile your protobuf files."""
    files = utils.get_files(paths)

    if not files:
        return rich.print("[bold]No files found to compile")

    for output_path, protos in files.items():
        output = output or (Path(output_path.parent.name) / output_path.name).resolve()
        output.mkdir(exist_ok=True, parents=True)

        errors = await compile_protobufs(
            *protos,
            output=output,
            verbose=verbose,
            generate_services=generate_services,
            line_length=line_length,
            from_cli=True,
        )

        for error in errors:
            if isinstance(error, protobuf_parser.SyntaxError):
                rich.print(
                    f"[red]File {str(error.file).strip()}:\n",
                    Syntax.from_path(
                        error.file,
                        line_numbers=True,
                        line_range=(max(error.lineno - 5, 0), error.lineno),
                    ),
                    f"{' ' * (error.offset + 3)}^\nSyntaxError: {error.msg}[red]",
                    file=sys.stderr,
                )
            elif isinstance(error, Warning):
                rich.print(f"Warning: {error}", file=sys.stderr)
            elif isinstance(error, protobuf_parser.Error):
                failed_files = "\n".join(f" - {file}" for file in protos)
                rich.print(
                    f"[red]Protoc failed to generate outputs for:\n\n"
                    f"{failed_files}\n\nSee the output for the issue:\n{error}[red]",
                    file=sys.stderr,
                )

        has_warnings = all(isinstance(e, Warning) for e in errors)
        if not errors or has_warnings:
            rich.print(
                f"[bold green]Finished generating output for "
                f"{len(protos)} file{'s' if len(protos) != 1 else ''}, "
                f"output is in {output.as_posix()}"
            )

        if errors:
            if not has_warnings:
                exit(2)
            exit(1)
        exit(0)
