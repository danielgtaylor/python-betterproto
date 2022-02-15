import asyncio
import functools
import sys
from collections.abc import Mapping
from collections import defaultdict
from pathlib import Path
from typing import Any, Awaitable, Callable, Iterable, List, Optional, Set, TypeVar

from typing_extensions import ParamSpec

T = TypeVar("T")
P = ParamSpec("P")


def get_files(paths: List[Path]) -> "Mapping[Path, Set[Path]]":
    """Return a list of files ready for :func:`generate_command`"""

    new_paths: "defaultdict[Path, Set[Path]]" = defaultdict(set)
    for path in paths:
        if not path.is_absolute():
            path = (Path.cwd() / path).resolve()

        if path.is_dir():
            new_paths[path].update(
                sorted(path.glob("*.proto"))
            )  # ensure order for files when debugging compilation errors
        else:
            new_paths[path.parent].add(path)

    return dict(new_paths)


def run_sync(func: Callable[P, Awaitable[T]]) -> Callable[P, T]:
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        coro = func(*args, **kwargs)

        if hasattr(asyncio, "run"):
            return asyncio.run(coro)

        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    return wrapper


def find(predicate: Callable[[T], bool], iterable: Iterable[T]) -> Optional[T]:
    for i in iterable:
        if predicate(i):
            return i


if sys.version_info >= (3, 9):
    to_thread = asyncio.to_thread
else:

    async def to_thread(func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        loop = asyncio.get_running_loop()
        func_call = functools.partial(func, *args, **kwargs)
        return await loop.run_in_executor(None, func_call)
