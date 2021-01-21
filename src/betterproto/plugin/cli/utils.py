import asyncio
import functools
import os
import platform
import sys
from collections import defaultdict
from pathlib import Path
from typing import Awaitable, Callable, TypeVar, Any, List, Set

# from . import USE_PROTOC
USE_PROTOC = True

T = TypeVar("T")

INCLUDE = (
    "any.proto",
    "api.proto",
    "compiler/plugin.proto",
    "descriptor.proto",
    "duration.proto",
    "empty.proto",
    "field_mask.proto",
    "source_context.proto",
    "struct.proto",
    "timestamp.proto",
    "type.proto",
    "wrappers.proto",
)


def get_files(paths: List[Path]) -> "defaultdict[Path, Set[Path]]":
    """Return a list of files ready for :func:`generate_command`"""
    # TODO create a default dict of parent to paths
    # recurse up folder to file first folder without a .proto
    # return highest directory as first value in list

    new_paths: "defaultdict[Path, Set[Path]]" = defaultdict(set)
    for path in paths:
        if not path.is_absolute():
            path = (Path.cwd() / path).resolve()
        if str(path).startswith("/usr") and "include/google/protobuf" in str(path):
            # TODO make this better for windows systems and being in different places in usr/
            # TODO make this actually work :) --plugin=protoc-gen-custom=src/betterproto/plugin/main.py
            new_paths[path].update(path / proto for proto in INCLUDE)
        elif path.is_dir():
            new_paths[path].update(path.glob("*.proto"))
        else:
            new_paths[path.parent].add(path)

    return new_paths


def generate_command(
    *files: Path,
    output: Path,
    use_protoc: bool = USE_PROTOC,
    implementation: str = "betterproto_",
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


if __name__ == '__main__':
    os.getcwd = lambda: "/Users/gobot1234/PycharmProjects/betterproto/tests/inputs"
    print(get_files(("bool", "bool/bool.proto", "casing/casing.proto")))
