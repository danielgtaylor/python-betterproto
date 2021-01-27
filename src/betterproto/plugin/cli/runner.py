import asyncio
import functools
import os
import re
from concurrent.futures import ProcessPoolExecutor
from typing import TYPE_CHECKING, Any, NoReturn, Tuple

from ...lib.google.protobuf.compiler import (
    CodeGeneratorRequest,
    CodeGeneratorResponseFile,
)
from ..parser import generate_code
from . import USE_PROTOC, utils
from .errors import CLIError, ProtobufSyntaxError

if TYPE_CHECKING:
    from pathlib import Path

DEFAULT_IMPLEMENTATION = "betterproto_"


def write_file(output: "Path", file: CodeGeneratorResponseFile) -> None:
    path = (output / file.name).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(file.content)
    except TypeError:
        pass


def handle_error(data: str, files: Tuple["Path", ...]) -> NoReturn:
    match = re.match(
        r"^(?P<filename>.+):(?P<lineno>\d+):(?P<offset>\d+):(?P<message>.*)",
        data,
    )
    if match is None:
        raise CLIError(data.strip())

    for file in files:
        if file.as_posix().endswith(match["filename"]):
            raise ProtobufSyntaxError(
                match["message"].strip(),
                file,
                int(match["lineno"]),
                int(match["offset"]),
            )
    raise ProtobufSyntaxError


async def compile_protobufs(
    *files: "Path",
    output: "Path",
    use_protoc: bool = USE_PROTOC,
    use_betterproto: bool = True,
    **kwargs: Any,
) -> Tuple[str, str]:
    """
    A programmatic way to compile protobufs.

    Parameters
    ----------
    *files: :class:`.Path`
        The locations of the protobuf files to be generated.
    output: :class:`.Path`
        The output directory.
    **kwargs:
        Any keyword arguments to pass to generate_code.

    Returns
    -------
    Tuple[:class:`str`, :class:`str`]
        A tuple of the ``stdout`` and ``stderr`` from the invocation of protoc.
    """
    implementation = DEFAULT_IMPLEMENTATION if use_betterproto else ""
    command = utils.generate_command(
        *files, output=output, use_protoc=use_protoc, implementation=implementation
    )

    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env={"USING_BETTERPROTO_CLI": str(kwargs.get("from_cli", False)), **os.environ},
    )

    stdout, stderr = await process.communicate()

    if use_betterproto:
        # we put code on stderr so we can actually read it thank you google :)))))

        try:
            request = CodeGeneratorRequest().parse(stderr)
        except Exception:
            handle_error(stderr.decode(), files)

        if request._unknown_fields:
            handle_error(stderr.decode(), files)

        # Generate code
        response = await utils.to_thread(generate_code, request, **kwargs)

        loop = asyncio.get_event_loop()
        with ProcessPoolExecutor() as process_pool:
            # write multiple files concurrently
            await asyncio.gather(
                *(
                    loop.run_in_executor(
                        process_pool, functools.partial(write_file, output, file)
                    )
                    for file in response.file
                )
            )

        stderr = b""

    if stderr:
        handle_error(stderr.decode(), files)

    if process.returncode != 0:
        raise CLIError(stderr.decode())

    return stdout.decode(), stderr.decode()
