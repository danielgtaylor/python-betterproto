import os
from pathlib import Path
from typing import List

import typer
import rich
from rich.progress import Progress
from rich.syntax import Syntax

from betterproto.plugin.cli import (
    DEFAULT_LINE_LENGTH,
    DEFAULT_OUT,
    USE_PROTOC,
    VERBOSE,
    utils,
)

from betterproto.plugin.models import monkey_patch_oneof_index
from betterproto.plugin.cli.errors import CLIError, ProtobufSyntaxError
from betterproto.plugin.cli.runner import compile_protobufs

monkey_patch_oneof_index()
app = typer.Typer()
compile_app = typer.Typer()
app.add_typer(compile_app, name="compile")


@app.callback(context_settings={"help_option_names": ["-h", "--help"]})
def callback(ctx: typer.Context) -> None:
    """The main entry point to all things betterproto"""
    if ctx.invoked_subcommand is None:
        rich.print(ctx.get_help())


@utils.run_sync
@app.command(context_settings={"help_option_names": ["-h", "--help"]})
async def compile(
    verbose: bool = typer.Option(VERBOSE, "-v", "--verbose"),
    protoc: bool = typer.Option(
        USE_PROTOC,
        "-p",
        "--protoc",
        help="Whether or not to use protoc to compile the protobufs if this is false "
        "it will attempt to use grpc instead",
    ),
    line_length: int = typer.Option(DEFAULT_LINE_LENGTH, "-l", "--line-length"),
    generate_services: bool = typer.Option(
        True, help="Whether or not to generate servicer stubs"
    ),
    output: str = typer.Option(
        DEFAULT_OUT,
        "-o",
        "--output",
        help="The name of the output directory",
        file_okay=False,
        allow_dash=True,
    ),
    paths: List[Path] = typer.Argument(
        ..., exists=True, allow_dash=True, resolve_path=True
    ),
) -> None:
    """The recommended way to compile your protobuf files."""
    if not paths:
        return rich.print("[bold]No files provided")

    files = utils.get_files(paths)
    if not files:
        return rich.print("[bold]No files found to compile")

    for output_path, protos in files.items():
        try:
            output = Path.cwd() / output_path.name if output == DEFAULT_OUT else output
            output.mkdir(exist_ok=True)
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
            error = Syntax(
                exc.file.read_text(),
                "proto",
                line_numbers=True,
                line_range=(max(exc.lineno - 5, 0), exc.lineno),
            )
            # I'd like to switch to .from_path but it appears to be bugged and doesnt pick lexer_name
            rich.print(
                f"[red]File {str(exc.file).strip()}:\n",
                error,
                f"{' ' * (exc.offset + 3)}^\n" f"SyntaxError: {exc.msg}[red]",
            )
        except CLIError as exc:
            failed_files = "\n".join(f" - {file}" for file in protos)
            rich.print(
                f"[red]{'Protoc' if protoc else 'GRPC'} failed to generate outputs for:\n\n"
                f"{failed_files}\n\nSee the output for the issue:\n{exc.args[0]}[red]",
            )

        else:
            rich.print(
                f"[bold green]Finished generating output for {len(protos)} files, output is in {output.as_posix()}"
            )


if __name__ == "__main__":
    os.getcwd = lambda: "/Users/gobot1234/PycharmProjects/betterproto"
    # sys.argv = "betterproto compile  --output=src/betterproto/lib".split()
    compile(
        output=Path("src/betterproto/lib").resolve(), paths=[Path("/usr/local/bin/include/google/protobuf")]
    )
