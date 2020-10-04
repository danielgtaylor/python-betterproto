#!/usr/bin/env python
import sys
import os

from betterproto.lib.google.protobuf.compiler import (
    CodeGeneratorRequest,
    CodeGeneratorResponse,
)
from betterproto.plugin.parser import generate_code


def main():
    """The plugin's main entry point."""
    # Read request message from stdin
    data = sys.stdin.buffer.read()

    request = CodeGeneratorRequest().parse(data)

    # sys.stderr.write(f"request: {request}")

    # TODO: scan request to find Option extensions,
    #       and if found then monkey patch the relevant messages and parse data again

    dump_file = os.getenv("BETTERPROTO_DUMP")
    if dump_file:
        dump_request(dump_file, request)

    # Create response
    response = CodeGeneratorResponse()

    # Generate code
    generate_code(request, response)

    # Serialise response message
    output = response.SerializeToString()

    # Write to stdout
    sys.stdout.buffer.write(output)


def dump_request(dump_file: str, request: CodeGeneratorRequest):
    """
    For developers: Supports running plugin.py standalone so its possible to debug it.
    Run protoc (or generate.py) with BETTERPROTO_DUMP="yourfile.bin" to write the request to a file.
    Then run plugin.py from your IDE in debugging mode, and redirect stdin to the file.
    """
    with open(str(dump_file), "wb") as fh:
        sys.stderr.write(f"\033[31mWriting input from protoc to: {dump_file}\033[0m\n")
        fh.write(request.SerializeToString())


if __name__ == "__main__":
    main()
