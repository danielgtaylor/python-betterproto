import asyncio
import functools
import platform
import sys
from pathlib import Path
from typing import Any, Awaitable, Callable, List, TypeVar

from . import USE_PROTOC

T = TypeVar("T")


def get_files(src: str) -> List[Path]:
    """Return a list of files ready for :func:`generate_command`"""
    path = Path(src)
    if not path.is_absolute():
        path = (Path.cwd() / src).resolve()
    if path.is_dir():
        return [p for p in path.iterdir() if p.suffix == ".proto"]
    return [path]


def generate_command(
    *files: Path, output: Path, use_protoc: bool = USE_PROTOC, implementation: str = "betterproto_"
) -> str:

    command = [
        f"--proto_path={files[0].parent.as_posix()}",
        f"--python_{implementation}out={output.as_posix()}",
        *[file.as_posix() for file in files],
    ]
    if use_protoc:
        command.insert(0, "protoc")
    else:
        command = [
            sys.executable,
            "-m",
            "grpc_tools.protoc",
            *command,
        ]

    return " ".join(command)


def run_sync(func: Callable[..., Awaitable[T]]) -> Callable[..., T]:
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        coro = func(*args, **kwargs)

        if hasattr(asyncio, "run"):
            return asyncio.run(coro)

        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    return wrapper


if sys.version_info[:2] >= (3, 9):
    from asyncio import to_thread
else:
    async def to_thread(func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        loop = asyncio.get_event_loop()
        # no context vars
        partial = functools.partial(func, *args, **kwargs)
        return await loop.run_in_executor(None, partial)
