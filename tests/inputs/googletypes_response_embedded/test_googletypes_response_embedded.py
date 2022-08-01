import pytest

from tests.mocks import MockChannel
from tests.output_betterproto.googletypes_response_embedded import (
    Input,
    Output,
    TestStub,
)


@pytest.mark.asyncio
async def test_service_passes_through_unwrapped_values_embedded_in_response():
    """
    We do not not need to implement value unwrapping for embedded well-known types,
    as this is already handled by grpclib. This test merely shows that this is the case.
    """
    output = Output(
        double_value=10.0,
        float_value=12.0,
        int64_value=-13,
        uint64_value=14,
        int32_value=-15,
        uint32_value=16,
        bool_value=True,
        string_value="string",
        bytes_value=bytes(0xFF)[0:4],
    )

    service = TestStub(MockChannel(responses=[output]))
    response = await service.get_output(Input())

    assert response.double_value == 10.0
    assert response.float_value == 12.0
    assert response.int64_value == -13
    assert response.uint64_value == 14
    assert response.int32_value == -15
    assert response.uint32_value == 16
    assert response.bool_value
    assert response.string_value == "string"
    assert response.bytes_value == bytes(0xFF)[0:4]
