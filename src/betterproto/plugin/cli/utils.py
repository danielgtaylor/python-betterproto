import asyncio
import functools
import sys
from pathlib import Path
from typing import Awaitable, Callable, Tuple, TypeVar, Any

from . import ENV

T = TypeVar("T")


def recursive_file_finder(directory: Path) -> Tuple[Path, ...]:
    files = set()
    for path in directory.iterdir():
        if path.is_file() and path.name.endswith(".proto"):
            files.add(path)
        elif path.is_dir():
            files.update(recursive_file_finder(path))

    return tuple(files)


def generate_command(
    *files: Path, output: Path, implementation: str = "betterproto_"
) -> str:
    cwd = Path.cwd()
    files = [file.relative_to(cwd).as_posix() for file in files]
    command = [
        f"--python_{implementation}out={output.as_posix()}",
        "-I",
        ".",
        *files,
    ]
    if ENV["USE_PROTOC"]:
        command.insert(0, "protoc")
    else:
        command.insert(0, "grpc.tools.protoc")
        command.insert(0, "-m")
        command.insert(0, sys.executable)

    return " ".join(command)


def run_sync(func: Callable[..., Awaitable[T]]) -> Callable[..., T]:
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        coro = func(*args, **kwargs)

        if hasattr(asyncio, "run"):
            return asyncio.run(coro, debug=True)

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
