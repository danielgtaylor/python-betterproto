from datetime import (
    datetime,
    timedelta,
)
from typing import (
    Any,
    Callable,
)

import pytest

import bananaproto.lib.google.protobuf as protobuf
from tests.mocks import MockChannel
from tests.output_bananaproto.googletypes_request import (
    Input,
    TestStub,
)


test_cases = [
    (TestStub.send_double, protobuf.DoubleValue, 2.5),
    (TestStub.send_float, protobuf.FloatValue, 2.5),
    (TestStub.send_int64, protobuf.Int64Value, -64),
    (TestStub.send_u_int64, protobuf.UInt64Value, 64),
    (TestStub.send_int32, protobuf.Int32Value, -32),
    (TestStub.send_u_int32, protobuf.UInt32Value, 32),
    (TestStub.send_bool, protobuf.BoolValue, True),
    (TestStub.send_string, protobuf.StringValue, "string"),
    (TestStub.send_bytes, protobuf.BytesValue, bytes(0xFF)[0:4]),
    (TestStub.send_datetime, protobuf.Timestamp, datetime(2038, 1, 19, 3, 14, 8)),
    (TestStub.send_timedelta, protobuf.Duration, timedelta(seconds=123456)),
]


@pytest.mark.asyncio
@pytest.mark.parametrize(["service_method", "wrapper_class", "value"], test_cases)
async def test_channel_receives_wrapped_type(
    service_method: Callable[[TestStub, Input], Any], wrapper_class: Callable, value
):
    wrapped_value = wrapper_class()
    wrapped_value.value = value
    channel = MockChannel(responses=[Input()])
    service = TestStub(channel)

    await service_method(service, wrapped_value)

    assert channel.requests[0]["request"] == type(wrapped_value)
