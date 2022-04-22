import copy
import sys

import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--repeat", type=int, default=1, help="repeat the operation multiple times"
    )


@pytest.fixture(scope="session")
def repeat(request):
    return request.config.getoption("repeat")


@pytest.fixture
def reset_sys_path():
    original = copy.deepcopy(sys.path)
    yield
    sys.path = original
