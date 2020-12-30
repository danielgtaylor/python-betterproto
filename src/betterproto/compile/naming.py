import re
from typing import Iterable, List

import itertools
from betterproto import casing


def pythonize_class_name(name: str) -> str:
    return casing.pascal_case(name)


def pythonize_field_name(name: str) -> str:
    return casing.safe_snake_case(name)


def pythonize_method_name(name: str) -> str:
    return casing.safe_snake_case(name)


def pythonize_enum_member_names(names: Iterable[str]) -> List[str]:
    """Removes any of the same characters from an Enum member's names."""

    def find_max_prefix_len() -> int:
        for max_prefix_len, chars in enumerate(tuple(zip(*map(tuple, names)))):
            previous_char = chars[0][0]
            for char in chars:
                if previous_char != char:
                    return max_prefix_len
        return 0

    max_prefix_len = find_max_prefix_len()

    return [casing.sanitize_name(name[max_prefix_len:]) for name in names]
