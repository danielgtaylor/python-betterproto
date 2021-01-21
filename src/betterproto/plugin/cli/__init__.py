import asyncio
import platform

try:
    import grpc_tools.protoc
except ImportError:
    USE_PROTOC = True
else:
    USE_PROTOC = False

DEFAULT_OUT = "betterproto_out"
VERBOSE = False
from black import DEFAULT_LINE_LENGTH as DEFAULT_LINE_LENGTH  # noqa

from .commands import app
from .runner import compile_protobufs

if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
