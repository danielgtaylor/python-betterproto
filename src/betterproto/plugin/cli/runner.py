import asyncio
import re
from pathlib import Path
from typing import Tuple

from . import ENV
from .errors import ProtobufSyntaxError, CLIError
from ...lib.google.protobuf.compiler import CodeGeneratorRequest
from ...plugin.parser import generate_code


async def compile_protobufs(
    *files: Path, output: Path, implementation: str = "betterproto_"
) -> Tuple[str, str]:
    """
    A programmatic way to compile protobufs.

    Parameters
    ----------
    *files
    output

    Returns
    -------
    Tuple[:class:`str`, :class:`str`]
        A tuple of the ``stdout`` and ``stderr`` from the invocation of protoc.
    """
    from . import utils  # circular import

    command = utils.generate_command(*files, output=output, implementation=implementation)

    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        stdin=asyncio.subprocess.PIPE,
        env=ENV,
        cwd=Path.cwd()
    )

    if implementation == "betterproto_":
        data = await process.stderr.read()  # we put code on stderr so we can actually read it
        # thank you google :)))))

        request = CodeGeneratorRequest().parse(data)
        if request._unknown_fields:
            match = re.match(r"(?P<filename>.+):(?P<lineno>\d+):(?P<offset>\d+):(?P<message>.*)", data.decode())
            # we had a parsing error
            for file in files:
                if file.as_posix().endswith(match["filename"]):
                    raise ProtobufSyntaxError(match["message"].strip(), file, int(match["lineno"]), int(match["offset"]))
            raise ProtobufSyntaxError
        # Generate code
        response = await utils.to_thread(generate_code, request)
        for file in response.file:
            (output / file.name).resolve().write_text(file.content)

        stdout, stderr = await process.communicate()

    else:
        stdout, stderr = await process.communicate()

    if process.returncode != 0:
        raise CLIError(stderr.decode())  # bad

    return stdout.decode(), stderr.decode()
