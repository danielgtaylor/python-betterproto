import asyncio
import os
import platform
from pathlib import Path
from typing import Any, Dict

from black import DEFAULT_LINE_LENGTH as DEFAULT_LINE_LENGTH  # noqa

try:
    import grpc
except ImportError:
    USE_PROTOC = True
else:
    USE_PROTOC = False

DEFAULT_OUT = Path.cwd() / "betterproto_out"
VERBOSE = False
ENV: Dict[str, Any] = dict(os.environ)

from .commands import main
from .runner import compile_protobufs

if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
