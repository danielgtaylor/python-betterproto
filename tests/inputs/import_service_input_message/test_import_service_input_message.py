import pytest

from tests.mocks import MockChannel
from tests.output_betterproto.import_service_input_message import (
    NestedRequestMessage,
    RequestMessage,
    RequestResponse,
    TestStub,
)
from tests.output_betterproto.import_service_input_message.child import (
    ChildRequestMessage,
)


@pytest.mark.asyncio
async def test_service_correctly_imports_reference_message():
    mock_response = RequestResponse(value=10)
    service = TestStub(MockChannel([mock_response]))
    response = await service.do_thing(RequestMessage(1))
    assert mock_response == response


@pytest.mark.asyncio
async def test_service_correctly_imports_reference_message_from_child_package():
    mock_response = RequestResponse(value=10)
    service = TestStub(MockChannel([mock_response]))
    response = await service.do_thing2(ChildRequestMessage(1))
    assert mock_response == response


@pytest.mark.asyncio
async def test_service_correctly_imports_nested_reference():
    mock_response = RequestResponse(value=10)
    service = TestStub(MockChannel([mock_response]))
    response = await service.do_thing3(NestedRequestMessage(1))
    assert mock_response == response
