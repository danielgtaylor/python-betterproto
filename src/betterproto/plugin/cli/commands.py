import os
import sys
from pathlib import Path
import logging
import click
import rich
from rich.progress import Progress
from rich.syntax import Syntax

from src.betterproto.plugin.cli import DEFAULT_LINE_LENGTH, DEFAULT_OUT, ENV, USE_PROTOC, VERBOSE
from src.betterproto.plugin.cli.errors import ProtobufSyntaxError
from src.betterproto.plugin.cli.runner import compile_protobufs
from src.betterproto.plugin.cli.utils import recursive_file_finder, run_sync
from src.betterproto.plugin.models import monkey_patch_oneof_index

monkey_patch_oneof_index()

logger = logging.getLogger('asyncio')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='out.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.pass_context
def main(ctx: click.Context) -> None:
    """The main entry point to all things betterproto"""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


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
    help="Whether or not to use protoc to compile the protobufs if this is false it will attempt to use grpc instead",
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
    is_eager=True,
)
@click.argument(
    "src",
    type=click.Path(exists=True, file_okay=True, dir_okay=True, allow_dash=True),
    is_eager=True,
)
@run_sync
async def compile(
    verbose: bool,
    protoc: bool,
    line_length: int,
    generate_services: bool,
    output: str,
    src: str,
) -> None:
    """The recommended way to compile your protobuf files."""

    directory = (Path.cwd() / src).resolve()
    files = recursive_file_finder(directory) if directory.is_dir() else (directory,)
    if not files:
        return rich.print("[bold]No files found to compile")

    output = Path.cwd() / output
    output.mkdir(exist_ok=True)

    ENV["VERBOSE"] = str(int(verbose))
    ENV["GENERATE_SERVICES"] = str(int(generate_services))
    ENV["USE_PROTOC"] = str(int(protoc and USE_PROTOC))
    ENV["LINE_LENGTH"] = str(line_length)
    ENV["USING_BETTERPROTO_CLI"] = str(1)

    try:
        await compile_protobufs(*files, output=output)
    except ProtobufSyntaxError as exc:
        error = Syntax.from_path(str(exc.file).strip(), line_numbers=True, line_range=(0, exc.lineno))
        return rich.print(f"Syntax Error in protobuf file {str(exc.file).strip()}:\n", error, f"{' ' * (exc.offset + 3)}^\n", exc.msg)
    except SyntaxError:
        failed_files = "\n".join(f" - {file}" for file in files)
        return rich.print(
            f"[red]{'Protoc' if ENV['USE_PROTOC'] else 'GRPC'} failed to generate outputs for:\n\n"
            f"{failed_files}\n\nSee the output for the issue:\n{exc.stderr}",
            file=sys.stderr,
        )

    rich.print(
        f"[bold]Finished generating output for {len(files)} files, compiled output should be in {output.as_posix()}"
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

if __name__ == '__main__':
    os.getcwd = lambda: "/Users/gobot1234/PycharmProjects/betterproto/tests"
    sys.argv = "betterproto compile /Users/gobot1234/PycharmProjects/betterproto/tests/inputs/bool".split()
    main()
