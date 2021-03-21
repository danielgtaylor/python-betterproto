import asyncio
import functools
import os
import re
import secrets
from concurrent.futures import ProcessPoolExecutor
from typing import TYPE_CHECKING, Any, List, Tuple

from ...lib.google.protobuf.compiler import (
    CodeGeneratorRequest,
    CodeGeneratorResponseFile,
    CodeGeneratorResponse,
)
from ..parser import generate_code
from . import USE_PROTOC, utils
from .errors import CLIError, CompilerError, ProtobufSyntaxError, UnusedImport

if TYPE_CHECKING:
    from pathlib import Path

DEFAULT_IMPLEMENTATION = "betterproto_"


def write_file(output: "Path", file: CodeGeneratorResponseFile) -> None:
    path = (output / file.name).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(file.content)


def handle_error(data: bytes, files: Tuple["Path", ...]) -> List[CLIError]:
    errors = []
    matches = re.finditer(
        rb"^(?P<filename>.+):(?P<lineno>\d+):(?P<offset>\d+): (?P<message>.*)",
        data,
    )
    if not matches:
        return [CompilerError(data.decode().strip())]

    for match in matches:
        file = utils.find(
            lambda f: f.as_posix().endswith(match["filename"].decode()), files
        )

        if match["message"].startswith(b"warning: "):
            import_matches = list(
                re.finditer(
                    rb"warning: Import (?P<unused_import>.+) is unused\.",
                    match["message"],
                )
            )
            if import_matches:
                for import_match in import_matches:
                    unused_import = utils.find(
                        lambda f: file.as_posix().endswith(
                            import_match["unused_import"].decode()
                        ),
                        files,
                    )
                    if unused_import is None:
                        unused_import = import_match["unused_import"].decode()
                    warning = UnusedImport(
                        match["message"].decode().strip(), file, unused_import
                    )
            else:
                warning = Warning(
                    match["message"].lstrip(b"warning: ").strip().decode()
                )

            errors.append(warning)
            continue

        errors.append(
            ProtobufSyntaxError(
                match["message"].decode().strip(),
                file,
                int(match["lineno"]),
                int(match["offset"]),
            )
        )

    return errors


async def compile_protobufs(
    *files: "Path",
    output: "Path",
    use_protoc: bool = USE_PROTOC,
    use_betterproto: bool = True,
    **kwargs: Any,
) -> List[CLIError]:
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
    implementation = DEFAULT_IMPLEMENTATION if use_betterproto else ""
    command = utils.generate_command(
        *files, output=output, use_protoc=use_protoc, implementation=implementation
    )

    secret_word = secrets.token_hex(256)

    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env={
            "USING_BETTERPROTO_CLI": str(kwargs.get("from_cli", False)),
            "BETTERPROTO_STOP_KEYWORD": secret_word,
            **os.environ,
        },
    )

    if use_betterproto:
        stderr = await process.stderr.read()
        if stderr.find(secret_word.encode()) == -1:
            return handle_error(stderr, files)

        try:
            stderr, data = stderr.split(secret_word.encode())
        except TypeError:
            return await compile_protobufs(
                *files,
                output=output,
                use_protoc=use_protoc,
                use_betterproto=use_betterproto,
                **kwargs,
            )  # you've exceptionally un/lucky

        if stderr:
            return handle_error(stderr, files)

        request = CodeGeneratorRequest().parse(data)

        loop = asyncio.get_event_loop()
        # Generate code
        response: CodeGeneratorResponse = await loop.run_in_executor(
            None, functools.partial(generate_code, request, **kwargs)
        )

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

    stdout, stderr = await process.communicate()

    if stderr:
        return handle_error(stderr, files)

    if process.returncode != 0:
        return [CompilerError(stderr.decode())]

    return []
