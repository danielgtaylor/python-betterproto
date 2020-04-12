import betterproto
import grpclib
from grpclib.testing import ChannelFor
import pytest
from typing import Dict
from .service import DoThingResponse, DoThingRequest, ExampleServiceStub


class ExampleService:

    async def DoThing(self, stream: 'grpclib.server.Stream[DoThingRequest, DoThingResponse]'):
        request = await stream.recv_message()
        for iteration in range(request.iterations):
            pass
        await stream.send_message(DoThingResponse(request.iterations))


    def __mapping__(self) -> Dict[str, grpclib.const.Handler]:
        return {
            '/service.ExampleService/DoThing': grpclib.const.Handler(
                self.DoThing,
                grpclib.const.Cardinality.UNARY_UNARY,
                DoThingRequest,
                DoThingResponse,
            ),
        }


@pytest.mark.asyncio
async def test_simple_service_call():
    ITERATIONS = 42
    async with ChannelFor([ExampleService()]) as channel:
        stub = ExampleServiceStub(channel)
        response = await stub.do_thing(iterations=ITERATIONS)
        assert response.successful_iterations == ITERATIONS
