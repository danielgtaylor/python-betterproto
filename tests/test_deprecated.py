import warnings

import pytest

from tests.mocks import MockChannel
from tests.output_betterproto.deprecated import (
    Empty,
    Message,
    Test,
    TestServiceStub,
)


@pytest.fixture
def message():
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        return Message(value="hello")


def test_deprecated_message():
    with pytest.warns(DeprecationWarning) as record:
        Message(value="hello")

    assert len(record) == 1
    assert str(record[0].message) == f"{Message.__name__} is deprecated"


def test_message_with_deprecated_field(message):
    with pytest.warns(DeprecationWarning) as record:
        Test(message=message, value=10)

    assert len(record) == 1
    assert str(record[0].message) == f"{Test.__name__}.message is deprecated"


def test_message_with_deprecated_field_not_set(message):
    with pytest.warns(None) as record:
        Test(value=10)

    assert not record


def test_message_with_deprecated_field_not_set_default(message):
    with pytest.warns(None) as record:
        _ = Test(value=10).message

    assert not record


def test_service_with_deprecated_method():
    stub = TestServiceStub(MockChannel())

    with pytest.warns(DeprecationWarning) as record:
        stub.deprecated_func(Empty())

    assert len(record) == 1
    assert str(record[0].message) == f"TestService.deprecated_func is deprecated"
