import betterproto
import grpclib
from grpclib.testing import ChannelFor
import pytest
from typing import Dict
from betterproto.tests.output_betterproto.service.service import (
    DoThingResponse,
    DoThingRequest,
    GetThingRequest,
    GetThingResponse,
    TestStub as ThingServiceClient,
)


class ThingService:
    def __init__(self, test_hook=None):
        # This lets us pass assertions to the servicer ;)
        self.test_hook = test_hook

    async def DoThing(
        self, stream: "grpclib.server.Stream[DoThingRequest, DoThingResponse]"
    ):
        request = await stream.recv_message()
        if self.test_hook is not None:
            self.test_hook(stream)
        await stream.send_message(DoThingResponse([request.name]))

    async def DoManyThings(
        self, stream: "grpclib.server.Stream[DoThingRequest, DoThingResponse]"
    ):
        thing_names = [request.name for request in stream]
        if self.test_hook is not None:
            self.test_hook(stream)
        await stream.send_message(DoThingResponse(thing_names))

    async def GetThingVersions(
        self, stream: "grpclib.server.Stream[GetThingRequest, GetThingResponse]"
    ):
        request = await stream.recv_message()
        if self.test_hook is not None:
            self.test_hook(stream)
        for version_num in range(1, 6):
            await stream.send_message(
                GetThingResponse(name=request, version=version_num)
            )

    async def GetDifferentThings(
        self, stream: "grpclib.server.Stream[GetThingRequest, GetThingResponse]"
    ):
        if self.test_hook is not None:
            self.test_hook(stream)
        #  Response to each input item immediately
        for request in stream:
            await stream.send_message(GetThingResponse(name=request.name, version=1))

    def __mapping__(self) -> Dict[str, grpclib.const.Handler]:
        return {
            "/service.Test/DoThing": grpclib.const.Handler(
                self.DoThing,
                grpclib.const.Cardinality.UNARY_UNARY,
                DoThingRequest,
                DoThingResponse,
            ),
            "/service.Test/DoManyThings": grpclib.const.Handler(
                self.DoManyThings,
                grpclib.const.Cardinality.STREAM_UNARY,
                DoThingRequest,
                DoThingResponse,
            ),
            "/service.Test/GetThingVersions": grpclib.const.Handler(
                self.GetThingVersions,
                grpclib.const.Cardinality.UNARY_STREAM,
                GetThingRequest,
                GetThingResponse,
            ),
            "/service.Test/GetDifferentThings": grpclib.const.Handler(
                self.GetDifferentThings,
                grpclib.const.Cardinality.STREAM_STREAM,
                GetThingRequest,
                GetThingResponse,
            ),
        }


async def _test_stub(stub, name="clean room", **kwargs):
    response = await stub.do_thing(name=name)
    assert response.names == [name]


def _assert_request_meta_recieved(deadline, metadata):
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
    async with ChannelFor([ThingService()]) as channel:
        await _test_stub(ThingServiceClient(channel))


@pytest.mark.asyncio
async def test_service_call_with_upfront_request_params():
    # Setting deadline
    deadline = grpclib.metadata.Deadline.from_timeout(22)
    metadata = {"authorization": "12345"}
    async with ChannelFor(
        [ThingService(test_hook=_assert_request_meta_recieved(deadline, metadata))]
    ) as channel:
        await _test_stub(
            ThingServiceClient(channel, deadline=deadline, metadata=metadata)
        )

    # Setting timeout
    timeout = 99
    deadline = grpclib.metadata.Deadline.from_timeout(timeout)
    metadata = {"authorization": "12345"}
    async with ChannelFor(
        [ThingService(test_hook=_assert_request_meta_recieved(deadline, metadata))]
    ) as channel:
        await _test_stub(
            ThingServiceClient(channel, timeout=timeout, metadata=metadata)
        )


@pytest.mark.asyncio
async def test_service_call_lower_level_with_overrides():
    THING_TO_DO = "get milk"

    # Setting deadline
    deadline = grpclib.metadata.Deadline.from_timeout(22)
    metadata = {"authorization": "12345"}
    kwarg_deadline = grpclib.metadata.Deadline.from_timeout(28)
    kwarg_metadata = {"authorization": "12345"}
    async with ChannelFor(
        [ThingService(test_hook=_assert_request_meta_recieved(deadline, metadata))]
    ) as channel:
        stub = ThingServiceClient(channel, deadline=deadline, metadata=metadata)
        response = await stub._unary_unary(
            "/service.Test/DoThing",
            DoThingRequest(THING_TO_DO),
            DoThingResponse,
            deadline=kwarg_deadline,
            metadata=kwarg_metadata,
        )
        assert response.names == [THING_TO_DO]

    # Setting timeout
    timeout = 99
    deadline = grpclib.metadata.Deadline.from_timeout(timeout)
    metadata = {"authorization": "12345"}
    kwarg_timeout = 9000
    kwarg_deadline = grpclib.metadata.Deadline.from_timeout(kwarg_timeout)
    kwarg_metadata = {"authorization": "09876"}
    async with ChannelFor(
        [
            ThingService(
                test_hook=_assert_request_meta_recieved(kwarg_deadline, kwarg_metadata)
            )
        ]
    ) as channel:
        stub = ThingServiceClient(channel, deadline=deadline, metadata=metadata)
        response = await stub._unary_unary(
            "/service.Test/DoThing",
            DoThingRequest(THING_TO_DO),
            DoThingResponse,
            timeout=kwarg_timeout,
            metadata=kwarg_metadata,
        )
        assert response.names == [THING_TO_DO]
