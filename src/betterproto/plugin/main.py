#!/usr/bin/env python

import os
import sys

from google.protobuf.compiler import plugin_pb2 as plugin

from .parser import generate_code


def main():
    """The plugin's main entry point."""
    # Read request message from stdin
    data = sys.stdin.buffer.read()

    # Parse request
    request = plugin.CodeGeneratorRequest()
    request.ParseFromString(data)

    dump_file = os.getenv("BETTERPROTO_DUMP")
    if dump_file:
        dump_request(dump_file, request)

    # Create response
    response = plugin.CodeGeneratorResponse()

    # Generate code
    generate_code(request, response)

    # Serialise response message
    output = response.SerializeToString()

    # Write to stdout
    sys.stdout.buffer.write(output)


def dump_request(dump_file: str, request: plugin.CodeGeneratorRequest):
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
