import copy
import sys

import pytest


@pytest.fixture
def reset_sys_path():
    original = copy.deepcopy(sys.path)
    yield
    sys.path = original
