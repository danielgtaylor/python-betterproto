import betterproto
import grpclib
from grpclib.testing import ChannelFor
import pytest
from typing import Dict

from betterproto.tests.output_betterproto.service.service import (
    DoThingResponse,
    DoThingRequest,
    ExampleServiceStub,
)


class ExampleService:
    def __init__(self, test_hook=None):
        # This lets us pass assertions to the servicer ;)
        self.test_hook = test_hook

    async def DoThing(
        self, stream: "grpclib.server.Stream[DoThingRequest, DoThingResponse]"
    ):
        request = await stream.recv_message()
        print("self.test_hook", self.test_hook)
        if self.test_hook is not None:
            self.test_hook(stream)
        for iteration in range(request.iterations):
            pass
        await stream.send_message(DoThingResponse(request.iterations))

    def __mapping__(self) -> Dict[str, grpclib.const.Handler]:
        return {
            "/service.ExampleService/DoThing": grpclib.const.Handler(
                self.DoThing,
                grpclib.const.Cardinality.UNARY_UNARY,
                DoThingRequest,
                DoThingResponse,
            )
        }


async def _test_stub(stub, iterations=42, **kwargs):
    response = await stub.do_thing(iterations=iterations)
    assert response.successful_iterations == iterations


def _get_server_side_test(deadline, metadata):
    def server_side_test(stream):
        assert stream.deadline._timestamp == pytest.approx(
            deadline._timestamp, 1
        ), "The provided deadline should be recieved serverside"
        assert (
            stream.metadata["authorization"] == metadata["authorization"]
        ), "The provided authorization metadata should be recieved serverside"

    return server_side_test


@pytest.mark.asyncio
async def test_simple_service_call():
    async with ChannelFor([ExampleService()]) as channel:
        await _test_stub(ExampleServiceStub(channel))


@pytest.mark.asyncio
async def test_service_call_with_upfront_request_params():
    # Setting deadline
    deadline = grpclib.metadata.Deadline.from_timeout(22)
    metadata = {"authorization": "12345"}
    async with ChannelFor(
        [ExampleService(test_hook=_get_server_side_test(deadline, metadata))]
    ) as channel:
        await _test_stub(
            ExampleServiceStub(channel, deadline=deadline, metadata=metadata)
        )

    # Setting timeout
    timeout = 99
    deadline = grpclib.metadata.Deadline.from_timeout(timeout)
    metadata = {"authorization": "12345"}
    async with ChannelFor(
        [ExampleService(test_hook=_get_server_side_test(deadline, metadata))]
    ) as channel:
        await _test_stub(
            ExampleServiceStub(channel, timeout=timeout, metadata=metadata)
        )


@pytest.mark.asyncio
async def test_service_call_lower_level_with_overrides():
    ITERATIONS = 99

    # Setting deadline
    deadline = grpclib.metadata.Deadline.from_timeout(22)
    metadata = {"authorization": "12345"}
    kwarg_deadline = grpclib.metadata.Deadline.from_timeout(28)
    kwarg_metadata = {"authorization": "12345"}
    async with ChannelFor(
        [ExampleService(test_hook=_get_server_side_test(deadline, metadata))]
    ) as channel:
        stub = ExampleServiceStub(channel, deadline=deadline, metadata=metadata)
        response = await stub._unary_unary(
            "/service.ExampleService/DoThing",
            DoThingRequest(ITERATIONS),
            DoThingResponse,
            deadline=kwarg_deadline,
            metadata=kwarg_metadata,
        )
        assert response.successful_iterations == ITERATIONS

    # Setting timeout
    timeout = 99
    deadline = grpclib.metadata.Deadline.from_timeout(timeout)
    metadata = {"authorization": "12345"}
    kwarg_timeout = 9000
    kwarg_deadline = grpclib.metadata.Deadline.from_timeout(kwarg_timeout)
    kwarg_metadata = {"authorization": "09876"}
    async with ChannelFor(
        [
            ExampleService(
                test_hook=_get_server_side_test(kwarg_deadline, kwarg_metadata)
            )
        ]
    ) as channel:
        stub = ExampleServiceStub(channel, deadline=deadline, metadata=metadata)
        response = await stub._unary_unary(
            "/service.ExampleService/DoThing",
            DoThingRequest(ITERATIONS),
            DoThingResponse,
            timeout=kwarg_timeout,
            metadata=kwarg_metadata,
        )
        assert response.successful_iterations == ITERATIONS
