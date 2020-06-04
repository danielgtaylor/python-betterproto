from typing import Dict

import grpclib.const
import grpclib.server
import pytest
from grpclib.testing import ChannelFor

import betterproto
from betterproto.tests.output_betterproto.repeated.repeated import (
    ExampleServiceStub,
    Test,
)


class ExampleService:
    async def DoThing(
        self, stream: "grpclib.server.Stream[Test, Test]"
    ):
        request = await stream.recv_message()
        await stream.send_message(request)

    def __mapping__(self) -> Dict[str, grpclib.const.Handler]:
        return {
            "/repeated.ExampleService/DoThing": grpclib.const.Handler(
                self.DoThing,
                grpclib.const.Cardinality.UNARY_UNARY,
                Test,
                Test,
            ),
        }


@pytest.mark.asyncio
async def test_sets_serialized_on_wire() -> None:
    async with ChannelFor([ExampleService()]) as channel:
        stub = ExampleServiceStub(channel)
        response = await stub.do_thing(names=['a', 'b', 'c'])
        assert betterproto.serialized_on_wire(response)
        assert response.names == ['a', 'b', 'c']
