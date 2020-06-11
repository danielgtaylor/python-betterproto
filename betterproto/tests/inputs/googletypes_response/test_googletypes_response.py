from typing import Any, Callable, Optional

import betterproto.lib.google.protobuf as protobuf
import pytest

from betterproto.tests.mocks import MockChannel
from betterproto.tests.output_betterproto.googletypes_response.googletypes_response import (
    TestStub,
)

test_cases = [
    (TestStub.get_double, protobuf.DoubleValue, 2.5),
    (TestStub.get_float, protobuf.FloatValue, 2.5),
    (TestStub.get_int64, protobuf.Int64Value, -64),
    (TestStub.get_u_int64, protobuf.UInt64Value, 64),
    (TestStub.get_int32, protobuf.Int32Value, -32),
    (TestStub.get_u_int32, protobuf.UInt32Value, 32),
    (TestStub.get_bool, protobuf.BoolValue, True),
    (TestStub.get_string, protobuf.StringValue, "string"),
    (TestStub.get_bytes, protobuf.BytesValue, bytes(0xFF)[0:4]),
]


@pytest.mark.asyncio
@pytest.mark.parametrize(["service_method", "wrapper_class", "value"], test_cases)
async def test_channel_receives_wrapped_type(
    service_method: Callable[[TestStub], Any], wrapper_class: Callable, value
):
    wrapped_value = wrapper_class()
    wrapped_value.value = value
    channel = MockChannel(responses=[wrapped_value])
    service = TestStub(channel)

    await service_method(service)

    assert channel.requests[0]["response_type"] != Optional[type(value)]
    assert channel.requests[0]["response_type"] == type(wrapped_value)


@pytest.mark.asyncio
@pytest.mark.xfail
@pytest.mark.parametrize(["service_method", "wrapper_class", "value"], test_cases)
async def test_service_unwraps_response(
    service_method: Callable[[TestStub], Any], wrapper_class: Callable, value
):
    """
    grpclib does not unwrap wrapper values returned by services
    """
    wrapped_value = wrapper_class()
    wrapped_value.value = value
    service = TestStub(MockChannel(responses=[wrapped_value]))

    response_value = await service_method(service)

    assert response_value == value
    assert type(response_value) == type(value)
