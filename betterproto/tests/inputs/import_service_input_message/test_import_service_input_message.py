import pytest

from betterproto.tests.mocks import MockChannel
from betterproto.tests.output_betterproto.import_service_input_message import (
    RequestResponse,
    TestStub,
)


@pytest.mark.asyncio
async def test_service_correctly_imports_reference_message():
    mock_response = RequestResponse(value=10)
    service = TestStub(MockChannel([mock_response]))
    response = await service.do_thing(argument=1)
    assert mock_response == response


@pytest.mark.asyncio
async def test_service_correctly_imports_reference_message_from_child_package():
    mock_response = RequestResponse(value=10)
    service = TestStub(MockChannel([mock_response]))
    response = await service.do_thing2(child_argument=1)
    assert mock_response == response


@pytest.mark.asyncio
async def test_service_correctly_imports_nested_reference():
    mock_response = RequestResponse(value=10)
    service = TestStub(MockChannel([mock_response]))
    response = await service.do_thing3(nested_argument=1)
    assert mock_response == response
