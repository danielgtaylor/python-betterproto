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
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        Test(value=10)


def test_message_with_deprecated_field_not_set_default(message):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        _ = Test(value=10).message


@pytest.mark.asyncio
async def test_service_with_deprecated_method():
    stub = TestServiceStub(MockChannel([Empty(), Empty()]))

    with pytest.warns(DeprecationWarning) as record:
        await stub.deprecated_func(Empty())

    assert len(record) == 1
    assert str(record[0].message) == f"TestService.deprecated_func is deprecated"

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        await stub.func(Empty())


def test_warnings_import_for_deprecated_message():
    """Verify that deprecated messages trigger the warnings import."""
    with pytest.warns(DeprecationWarning):
        # This should trigger the warnings import in the generated code
        Message(value="test")

    # Check that warnings module is properly imported in the generated file
    import tests.output_betterproto.deprecated as deprecated_module

    assert "warnings" in deprecated_module.__dict__, (
        "warnings module should be imported for deprecated messages"
    )
