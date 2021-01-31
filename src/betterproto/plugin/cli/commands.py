from pathlib import Path
from typing import List, Optional

import typer
import rich
from rich.syntax import Syntax

from ..models import monkey_patch_oneof_index
from . import (
    DEFAULT_LINE_LENGTH,
    USE_PROTOC,
    VERBOSE,
    utils,
)
from .errors import CLIError, ProtobufSyntaxError
from .runner import compile_protobufs

monkey_patch_oneof_index()
app = typer.Typer()


@app.callback(context_settings={"help_option_names": ["-h", "--help"]})
def callback(ctx: typer.Context) -> None:
    """The callback for all things betterproto"""
    if ctx.invoked_subcommand is None:
        rich.print(ctx.get_help())


@app.command(context_settings={"help_option_names": ["-h", "--help"]})
@utils.run_sync
async def compile(
    verbose: bool = typer.Option(
        VERBOSE, "-v", "--verbose", help="Whether or not to be verbose"
    ),
    protoc: bool = typer.Option(
        USE_PROTOC,
        "-p",
        "--protoc",
        help="Whether or not to use protoc to compile the protobufs if this is false "
        "it will attempt to use grpc instead",
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
        try:
            output = (
                output or (Path(output_path.parent.name) / output_path.name).resolve()
            )
            output.mkdir(exist_ok=True, parents=True)
            await compile_protobufs(
                *protos,
                output=output,
                verbose=verbose,
                use_protoc=protoc,
                generate_services=generate_services,
                line_length=line_length,
                from_cli=True,
            )
        except ProtobufSyntaxError as exc:
            rich.print(
                f"[red]File {str(exc.file).strip()}:\n",
                Syntax(
                    exc.file.read_text(),
                    "proto",
                    line_numbers=True,
                    line_range=(max(exc.lineno - 5, 0), exc.lineno),
                ),  # TODO switch to .from_path but it appears to be bugged and doesnt render properly
                f"{' ' * (exc.offset + 3)}^\nSyntaxError: {exc.msg}[red]",
            )
        except CLIError as exc:
            failed_files = "\n".join(f" - {file}" for file in protos)
            rich.print(
                f"[red]{'Protoc' if protoc else 'GRPC'} failed to generate outputs for:\n\n"
                f"{failed_files}\n\nSee the output for the issue:\n{' '.join(exc.args)}[red]",
            )

        else:
            rich.print(
                f"[bold green]Finished generating output for {len(protos)} files, "
                f"output is in {output.as_posix()}"
            )
