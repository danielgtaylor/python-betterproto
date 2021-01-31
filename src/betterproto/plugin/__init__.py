import sys
import traceback
from pathlib import Path
from types import TracebackType
from typing import Type

IMPORT_ERROR_MESSAGE = (
    "Unable to import `{0.name}` from betterproto plugin! Please ensure that you've installed "
    'betterproto as `pip install "betterproto[compiler]"` so that compiler dependencies are '
    "included."
)

STDLIB_MODULES = getattr(
    sys,
    "module_names",
    [
        p.with_suffix("").name
        for p in Path(traceback.__file__).parent.iterdir()
        if p.suffix == ".py" or p.is_dir()
    ],
)


def import_exception_hook(
    type: Type[BaseException], value: ImportError, tb: TracebackType
) -> None:
    """Set an exception hook to automatically print:

    "Unable to import `x` from betterproto plugin! Please ensure that you've installed
    betterproto as `pip install "betterproto[compiler]"` so that compiler dependencies are
    included."

    if the module imported is not found and the exception is raised in this sub module
    """
    module = list(traceback.walk_tb(tb))[-1][0].f_globals.get("__name__", "__main__")
    if (
        not module.startswith(__name__)
        or not isinstance(value, ImportError)
        or value.name in STDLIB_MODULES
        or value.name.startswith("betterproto")
    ):
        return sys.__excepthook__(type, value, tb)

    print(f"\033[31m{IMPORT_ERROR_MESSAGE.format(value)}\033[0m", file=sys.stderr)
    exit(1)


sys.excepthook = import_exception_hook

from .main import main
