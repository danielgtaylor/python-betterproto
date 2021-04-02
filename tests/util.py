import importlib
import os
import pathlib
from pathlib import Path
from types import ModuleType
from typing import Callable, Generator, List, Optional, Union

os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

root_path = Path(__file__).resolve().parent
inputs_path = root_path.joinpath("inputs")
output_path_reference = root_path.joinpath("output_reference")
output_path_betterproto = root_path.joinpath("output_betterproto")


def get_directories(path: Path) -> Generator[str, None, None]:
    for root, directories, files in os.walk(path):
        yield from directories


def get_test_case_json_data(test_case_name: str, *json_file_names: str) -> List[str]:
    """
    :return:
        A list of all files found in "inputs_path/test_case_name" with names matching
        f"{test_case_name}.json" or f"{test_case_name}_*.json", OR given by json_file_names
    """
    test_case_dir = inputs_path.joinpath(test_case_name)
    possible_file_paths = [
        *(test_case_dir.joinpath(json_file_name) for json_file_name in json_file_names),
        test_case_dir.joinpath(f"{test_case_name}.json"),
        *test_case_dir.glob(f"{test_case_name}_*.json"),
    ]

    result = []
    for test_data_file_path in possible_file_paths:
        if not test_data_file_path.exists():
            continue
        with test_data_file_path.open("r") as fh:
            result.append(fh.read())

    return result


def find_module(
    module: ModuleType, predicate: Callable[[ModuleType], bool]
) -> Optional[ModuleType]:
    """
    Recursively search module tree for a module that matches the search predicate.
    Assumes that the submodules are directories containing __init__.py.

    Example:

        # find module inside foo that contains Test
        import foo
        test_module = find_module(foo, lambda m: hasattr(m, 'Test'))
    """
    if predicate(module):
        return module

    module_path = pathlib.Path(*module.__path__)

    for sub in [sub.parent for sub in module_path.glob("**/__init__.py")]:
        if sub == module_path:
            continue
        sub_module_path = sub.relative_to(module_path)
        sub_module_name = ".".join(sub_module_path.parts)

        sub_module = importlib.import_module(f".{sub_module_name}", module.__name__)

        if predicate(sub_module):
            return sub_module

    return None
