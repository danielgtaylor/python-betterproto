import pytest

from betterproto.tests.mocks import MockChannel
from betterproto.tests.output_betterproto.import_service_input_message import (
    RequestResponse,
    TestStub,
)


@pytest.mark.xfail(reason="#68 Request Input Messages are not imported for service")
@pytest.mark.asyncio
async def test_service_correctly_imports_reference_message():
    mock_response = RequestResponse(value=10)
    service = TestStub(MockChannel([mock_response]))
    response = await service.do_thing()
    assert mock_response == response
