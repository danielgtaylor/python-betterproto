import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--repeat", type=int, default=1, help="repeat the operation multiple times"
    )


@pytest.fixture(scope="session")
def repeat(request):
    return request.config.getoption("repeat")
