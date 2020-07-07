import asyncio
from betterproto.tests.output_betterproto.service.service import (
    DoThingResponse,
    DoThingRequest,
    GetThingRequest,
    TestStub as ThingServiceClient,
)
import grpclib
from grpclib.testing import ChannelFor
import pytest
from betterproto.grpc.util.async_channel import AsyncChannel
from .thing_service import ThingService


async def _test_client(client, name="clean room", **kwargs):
    response = await client.do_thing(name=name)
    assert response.names == [name]


def _assert_request_meta_received(deadline, metadata):
    def server_side_test(stream):
        assert stream.deadline._timestamp == pytest.approx(
            deadline._timestamp, 1
        ), "The provided deadline should be received serverside"
        assert (
            stream.metadata["authorization"] == metadata["authorization"]
        ), "The provided authorization metadata should be received serverside"

    return server_side_test


@pytest.mark.asyncio
async def test_simple_service_call():
    async with ChannelFor([ThingService()]) as channel:
        await _test_client(ThingServiceClient(channel))


@pytest.mark.asyncio
async def test_service_call_with_upfront_request_params():
    # Setting deadline
    deadline = grpclib.metadata.Deadline.from_timeout(22)
    metadata = {"authorization": "12345"}
    async with ChannelFor(
        [ThingService(test_hook=_assert_request_meta_received(deadline, metadata),)]
    ) as channel:
        await _test_client(
            ThingServiceClient(channel, deadline=deadline, metadata=metadata)
        )

    # Setting timeout
    timeout = 99
    deadline = grpclib.metadata.Deadline.from_timeout(timeout)
    metadata = {"authorization": "12345"}
    async with ChannelFor(
        [ThingService(test_hook=_assert_request_meta_received(deadline, metadata),)]
    ) as channel:
        await _test_client(
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
        [ThingService(test_hook=_assert_request_meta_received(deadline, metadata),)]
    ) as channel:
        client = ThingServiceClient(channel, deadline=deadline, metadata=metadata)
        response = await client._unary_unary(
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
                test_hook=_assert_request_meta_received(kwarg_deadline, kwarg_metadata),
            )
        ]
    ) as channel:
        client = ThingServiceClient(channel, deadline=deadline, metadata=metadata)
        response = await client._unary_unary(
            "/service.Test/DoThing",
            DoThingRequest(THING_TO_DO),
            DoThingResponse,
            timeout=kwarg_timeout,
            metadata=kwarg_metadata,
        )
        assert response.names == [THING_TO_DO]


@pytest.mark.asyncio
async def test_async_gen_for_unary_stream_request():
    thing_name = "my milkshakes"

    async with ChannelFor([ThingService()]) as channel:
        client = ThingServiceClient(channel)
        expected_versions = [5, 4, 3, 2, 1]
        async for response in client.get_thing_versions(name=thing_name):
            assert response.name == thing_name
            assert response.version == expected_versions.pop()


@pytest.mark.asyncio
async def test_async_gen_for_stream_stream_request():
    some_things = ["cake", "cricket", "coral reef"]
    more_things = ["ball", "that", "56kmodem", "liberal humanism", "cheesesticks"]
    expected_things = (*some_things, *more_things)

    async with ChannelFor([ThingService()]) as channel:
        client = ThingServiceClient(channel)
        # Use an AsyncChannel to decouple sending and recieving, it'll send some_things
        # immediately and we'll use it to send more_things later, after recieving some
        # results
        request_chan = AsyncChannel()
        send_initial_requests = asyncio.ensure_future(
            request_chan.send_from(GetThingRequest(name) for name in some_things)
        )
        response_index = 0
        async for response in client.get_different_things(request_chan):
            assert response.name == expected_things[response_index]
            assert response.version == response_index + 1
            response_index += 1
            if more_things:
                # Send some more requests as we receive responses to be sure coordination of
                # send/receive events doesn't matter
                await request_chan.send(GetThingRequest(more_things.pop(0)))
            elif not send_initial_requests.done():
                # Make sure the sending task it completed
                await send_initial_requests
            else:
                # No more things to send make sure channel is closed
                request_chan.close()
        assert response_index == len(
            expected_things
        ), "Didn't receive all expected responses"
