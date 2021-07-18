import asyncio
import functools

from concurrent.futures import ProcessPoolExecutor
from typing import TYPE_CHECKING, Any, List

import protobuf_parser

from ...lib.google.protobuf import FileDescriptorProto
from ...lib.google.protobuf.compiler import (
    CodeGeneratorRequest,
    CodeGeneratorResponseFile,
)
from ..parser import generate_code
from . import utils

if TYPE_CHECKING:
    from pathlib import Path


def write_file(output: "Path", file: CodeGeneratorResponseFile) -> None:
    path = (output / file.name).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(file.content)


async def compile_protobufs(
    *files: "Path",
    output: "Path",
    use_betterproto: bool = True,
    **kwargs: Any,
) -> List[protobuf_parser.Error]:
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
    List[:class:`CLIError`]
        A of exceptions from protoc.
    """
    loop = asyncio.get_event_loop()

    if use_betterproto:
        files, errors = await utils.to_thread(protobuf_parser.parse, *files)
        if errors:
            return errors
        request = CodeGeneratorRequest(
            proto_file=[
                FileDescriptorProto().parse(file) for file in files
            ]
        )

        # Generate code
        response = await utils.to_thread(generate_code, request, **kwargs)

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

    else:
        errors = await utils.to_thread(
            protobuf_parser.run,
            *(f'"{file.as_posix()}"' for file in files),
            proto_path=files[0].parent.as_posix(),
            python_out=output.as_posix()
        )

    return errors
