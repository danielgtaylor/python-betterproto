import pytest
from unittest.mock import MagicMock

from tests.output_betterproto.service_grpcio import (
    DoThingRequest,
    DoThingResponse,
    GetThingRequest,
    GetThingResponse,
    TestStub as ThingServiceGrpcioClient,
)

from .thing_service_grpcio import ThingServiceGrpcio, create_test_channel


async def _test_grpcio_client(client: ThingServiceGrpcioClient, name="clean room", **kwargs):
    response = await client.do_thing(DoThingRequest(name=name), **kwargs)
    assert response.names == [name]


def _assert_request_meta_received_grpcio(timeout, metadata):
    def server_side_test(context):
        if hasattr(context, 'timeout') and timeout:
            assert context.timeout == pytest.approx(timeout, 1), (
                "The provided timeout should be received serverside"
            )
        if hasattr(context, 'metadata') and metadata:
            for key, value in metadata.items():
                assert context.metadata.get(key) == value, (
                    f"The provided {key} metadata should be received serverside"
                )
    return server_side_test


@pytest.mark.asyncio
async def test_simple_grpcio_service_call():
    service = ThingServiceGrpcio()
    channel = create_test_channel(service)

    client = ThingServiceGrpcioClient(channel=MagicMock())

    async def mock_unary_unary(method, request, response_type, **kwargs):
        context = MagicMock()
        context.timeout = kwargs.get('timeout')
        context.metadata = kwargs.get('metadata', {})
        return channel.route_call(method, request, context)

    client._unary_unary = mock_unary_unary
    await _test_grpcio_client(client)


@pytest.mark.asyncio
async def test_grpcio_service_call_mutable_defaults(mocker):
    """Test that mutable defaults don't cause issues using ThingServiceGrpcio"""
    service = ThingServiceGrpcio()
    channel = create_test_channel(service)
    client = ThingServiceGrpcioClient(channel=MagicMock())

    spy = mocker.spy(client, '_unary_unary')

    async def mock_unary_unary(method, request, response_type, **kwargs):
        context = MagicMock()
        return channel.route_call(method, request, context)

    client._unary_unary = mock_unary_unary

    await _test_grpcio_client(client, name="test1")
    await _test_grpcio_client(client, name="test2")

    # Verify calls were made with different request objects
    if len(spy.call_args_list) >= 2:
        comments1 = spy.call_args_list[0].args[1].comments if len(spy.call_args_list[0].args) > 1 else []
        comments2 = spy.call_args_list[1].args[1].comments if len(spy.call_args_list[1].args) > 1 else []
        assert comments1 is not comments2


@pytest.mark.asyncio
async def test_grpcio_service_call_with_upfront_request_params():
    timeout = 30
    metadata = {"authorization": "12345"}

    def test_hook(context):
        assert context.timeout == timeout
        assert context.metadata.get("authorization") == "12345"

    service = ThingServiceGrpcio(test_hook=test_hook)
    channel = create_test_channel(service)
    client = ThingServiceGrpcioClient(channel=MagicMock(), timeout=timeout, metadata=metadata)

    async def mock_unary_unary(method, request, response_type, **kwargs):
        final_kwargs = client._resolve_request_kwargs(
            kwargs.get('timeout'),
            kwargs.get('metadata')
        )
        context = MagicMock()
        context.timeout = final_kwargs.get('timeout')
        context.metadata = final_kwargs.get('metadata', {})
        return channel.route_call(method, request, context)

    client._unary_unary = mock_unary_unary
    await _test_grpcio_client(client)


@pytest.mark.asyncio
async def test_grpcio_unary_stream_request():
    thing_name = "my milkshakes"

    service = ThingServiceGrpcio()
    channel = create_test_channel(service)
    client = ThingServiceGrpcioClient(channel=MagicMock())

    async def mock_unary_stream(method, request, response_type, **kwargs):
        context = MagicMock()
        for response in channel.route_call(method, request, context):
            yield response

    client._unary_stream = mock_unary_stream

    expected_versions = [5, 4, 3, 2, 1]
    async for response in client.get_thing_versions(GetThingRequest(name=thing_name)):
        assert response.name == thing_name
        assert response.version == expected_versions.pop(0)


@pytest.mark.asyncio
async def test_grpcio_stream_stream_request():
    some_things = ["cake", "cricket", "coral reef"]
    expected_things = some_things

    service = ThingServiceGrpcio()
    channel = create_test_channel(service)
    client = ThingServiceGrpcioClient(channel=MagicMock())

    async def mock_stream_stream(method, request_iterator, request_type, response_type, **kwargs):
        # Convert async iterator to list
        requests = [req async for req in client._wrap_message_iterator(request_iterator)]
        context = MagicMock()
        for response in channel.route_call(method, requests, context):
            yield response

    client._stream_stream = mock_stream_stream

    requests = [GetThingRequest(name) for name in some_things]
    response_index = 0
    async for response in client.get_different_things(requests):
        assert response.name == expected_things[response_index]
        assert response.version == response_index + 1
        response_index += 1

    assert response_index == len(expected_things), (
        "Didn't receive all expected responses"
    )


@pytest.mark.asyncio
async def test_grpcio_stream_unary_with_empty_iterable():
    things = []

    service = ThingServiceGrpcio()
    channel = create_test_channel(service)
    client = ThingServiceGrpcioClient(channel=MagicMock())

    async def mock_stream_unary(method, request_iterator, request_type, response_type, **kwargs):
        requests = [req async for req in client._wrap_message_iterator(request_iterator)]
        context = MagicMock()
        return channel.route_call(method, requests, context)

    client._stream_unary = mock_stream_unary

    requests = [DoThingRequest(name) for name in things]
    response = await client.do_many_things(requests)
    assert len(response.names) == 0


@pytest.mark.asyncio
async def test_grpcio_stream_stream_with_empty_iterable():
    things = []
    service = ThingServiceGrpcio()
    channel = create_test_channel(service)
    client = ThingServiceGrpcioClient(channel=MagicMock())

    async def mock_stream_stream(method, request_iterator, request_type, response_type, **kwargs):
        requests = [req async for req in client._wrap_message_iterator(request_iterator)]
        context = MagicMock()
        for response in channel.route_call(method, requests, context):
            yield response

    client._stream_stream = mock_stream_stream

    requests = [GetThingRequest(name) for name in things]
    responses = [
        response async for response in client.get_different_things(requests)
    ]
    assert len(responses) == 0


@pytest.mark.asyncio
async def test_grpcio_messages_validation():
    request = DoThingRequest(name="test message", comments=["comment1", "comment2"])
    assert request.name == "test message"
    assert request.comments == ["comment1", "comment2"]
    response = DoThingResponse(names=["response1", "response2"])
    assert response.names == ["response1", "response2"]
    get_request = GetThingRequest(name="get test")
    assert get_request.name == "get test"
    get_response = GetThingResponse(name="thing", version=1)
    assert get_response.name == "thing"
    assert get_response.version == 1


@pytest.mark.asyncio
async def test_grpcio_client_method_signatures():
    client = ThingServiceGrpcioClient(channel=MagicMock())
    assert hasattr(client, "do_thing")
    assert hasattr(client, "do_many_things")
    assert hasattr(client, "get_thing_versions")
    assert hasattr(client, "get_different_things")

    import inspect

    do_thing_sig = inspect.signature(client.do_thing)
    assert "do_thing_request" in do_thing_sig.parameters
    assert "timeout" in do_thing_sig.parameters
    assert "metadata" in do_thing_sig.parameters

    do_many_sig = inspect.signature(client.do_many_things)
    assert "do_thing_request_iterator" in do_many_sig.parameters
