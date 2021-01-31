#!/usr/bin/env python

import os
import signal
import sys
import time
from socket import socket

import rich

from ..lib.google.protobuf.compiler import CodeGeneratorRequest
from .models import monkey_patch_oneof_index
from .parser import generate_code


def main() -> None:
    """The plugin's main entry point."""
    # Read request message from stdin
    data = sys.stdin.buffer.read()

    if os.getenv("USING_BETTERPROTO_CLI") == "True":
        sys.stderr.buffer.write(os.environ["BETTERPROTO_STOP_KEYWORD"].encode())
        sys.stderr.buffer.write(data)

        sys.stdout.buffer.write(b"")
    else:
        # Apply Work around for proto2/3 difference in protoc messages
        monkey_patch_oneof_index()

        # Parse request
        request = CodeGeneratorRequest().parse(data)

        rich.print(
            "Direct invocation of the protoc plugin is depreciated over using the CLI\n"
            "To do so you just need to type:\n"
            f"betterproto compile {' '.join(request.file_to_generate)}",
            file=sys.stderr,
        )

        # Generate code
        response = generate_code(request)

        # Write to stdout
        sys.stdout.buffer.write(bytes(response))
