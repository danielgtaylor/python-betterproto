from typing import List, Optional, Set
import pytest
from betterproto.plugin.module_validation import ModuleValidator


@pytest.mark.parametrize(
    ["text", "expected_collisions"],
    [
        pytest.param(
            ["import os"],
            None,
            id="single import",
        ),
        pytest.param(
            ["import os", "import sys"],
            None,
            id="multiple imports",
        ),
        pytest.param(
            ["import os", "import os"],
            {"os"},
            id="duplicate imports",
        ),
        pytest.param(
            ["from os import path", "import os"],
            None,
            id="duplicate imports with alias",
        ),
        pytest.param(
            ["from os import path", "import os as os_alias"],
            None,
            id="duplicate imports with alias",
        ),
        pytest.param(
            ["from os import path", "import os as path"],
            {"path"},
            id="duplicate imports with alias",
        ),
        pytest.param(
            ["import os", "class os:"],
            {"os"},
            id="duplicate import with class",
        ),
        pytest.param(
            ["import os", "class os:", "  pass", "import sys"],
            {"os"},
            id="duplicate import with class and another",
        ),
        pytest.param(
            ["def test(): pass", "class test:"],
            {"test"},
            id="duplicate class and function",
        ),
        pytest.param(
            ["def test(): pass", "def test(): pass"],
            {"test"},
            id="duplicate functions",
        ),
        pytest.param(
            ["def test(): pass", "test = 100"],
            {"test"},
            id="function and variable",
        ),
        pytest.param(
            ["def test():", "    test = 3"],
            None,
            id="function and variable in function",
        ),
        pytest.param(
            [
                "def test(): pass",
                "'''",
                "def test(): pass",
                "'''",
                "def test_2(): pass",
            ],
            None,
            id="duplicate functions with multiline string",
        ),
        pytest.param(
            ["def test(): pass", "# def test(): pass"],
            None,
            id="duplicate functions with comments",
        ),
        pytest.param(
            ["from test import (", "    A", "   B", "   C", ")"],
            None,
            id="multiline import",
        ),
        pytest.param(
            ["from test import (", "    A", "   B", "   C", ")", "from test import A"],
            {"A"},
            id="multiline import with duplicate",
        ),
    ],
)
def test_module_validator(text: List[str], expected_collisions: Optional[Set[str]]):
    line_iterator = iter(text)
    validator = ModuleValidator(line_iterator)
    valid = validator.validate()
    if expected_collisions is None:
        assert valid
    else:
        assert set(validator.collisions.keys()) == expected_collisions
        assert not valid
