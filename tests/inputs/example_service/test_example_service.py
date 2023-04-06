from typing import (
    AsyncIterable,
    AsyncIterator,
)

import pytest
from grpclib.testing import ChannelFor

from bananaproto.grpc.grpclib_client import MetadataLike
from tests.output_bananaproto.example_service import (
    ExampleRequest,
    ExampleResponse,
    TestBase,
    TestStub,
)


class ExampleService(TestBase):
    async def example_unary_unary(
        self,
        example_request: ExampleRequest,
        metadata: MetadataLike,
    ) -> "ExampleResponse":
        return ExampleResponse(
            example_string=example_request.example_string,
            example_integer=example_request.example_integer,
            example_metadata_field=metadata.get("field", ""),
        )

    async def example_unary_stream(
        self,
        example_request: ExampleRequest,
        metadata: MetadataLike,
    ) -> AsyncIterator["ExampleResponse"]:
        response = ExampleResponse(
            example_string=example_request.example_string,
            example_integer=example_request.example_integer,
            example_metadata_field=metadata.get("field", ""),
        )
        yield response
        yield response
        yield response

    async def example_stream_unary(
        self,
        example_request_iterator: AsyncIterator["ExampleRequest"],
        metadata: MetadataLike,
    ) -> "ExampleResponse":
        async for example_request in example_request_iterator:
            return ExampleResponse(
                example_string=example_request.example_string,
                example_integer=example_request.example_integer,
                example_metadata_field=metadata.get("field", ""),
            )

    async def example_stream_stream(
        self,
        example_request_iterator: AsyncIterator["ExampleRequest"],
        metadata: MetadataLike,
    ) -> AsyncIterator["ExampleResponse"]:
        async for example_request in example_request_iterator:
            yield ExampleResponse(
                example_string=example_request.example_string,
                example_integer=example_request.example_integer,
                example_metadata_field=metadata.get("field", ""),
            )


@pytest.mark.asyncio
async def test_calls_with_different_cardinalities():
    example_request = ExampleRequest("test string", 42)

    async with ChannelFor([ExampleService()]) as channel:
        stub = TestStub(channel)

        # unary unary
        response = await stub.example_unary_unary(example_request)
        assert response.example_string == example_request.example_string
        assert response.example_integer == example_request.example_integer

        # unary stream
        async for response in stub.example_unary_stream(example_request):
            assert response.example_string == example_request.example_string
            assert response.example_integer == example_request.example_integer

        # stream unary
        async def request_iterator():
            yield example_request
            yield example_request
            yield example_request

        response = await stub.example_stream_unary(request_iterator())
        assert response.example_string == example_request.example_string
        assert response.example_integer == example_request.example_integer

        # stream stream
        async for response in stub.example_stream_stream(request_iterator()):
            assert response.example_string == example_request.example_string
            assert response.example_integer == example_request.example_integer


@pytest.mark.asyncio
async def test_stub_metadata():
    example_request = ExampleRequest()
    stub_metadata = {"field": "1"}

    async with ChannelFor([ExampleService()]) as channel:
        stub = TestStub(channel, metadata=stub_metadata)

        # unary unary
        response = await stub.example_unary_unary(example_request)
        assert response.example_metadata_field == stub_metadata["field"]

        # unary stream
        async for response in stub.example_unary_stream(example_request):
            assert response.example_metadata_field == stub_metadata["field"]

        # stream unary
        async def request_iterator():
            yield example_request
            yield example_request
            yield example_request

        response = await stub.example_stream_unary(request_iterator())
        assert response.example_metadata_field == stub_metadata["field"]

        # stream stream
        async for response in stub.example_stream_stream(request_iterator()):
            assert response.example_metadata_field == stub_metadata["field"]


@pytest.mark.asyncio
async def test_method_metadata():
    example_request = ExampleRequest()
    method_metadata = {"field": "2"}

    async with ChannelFor([ExampleService()]) as channel:
        stub = TestStub(channel)

        # unary unary
        response = await stub.example_unary_unary(
            example_request, metadata=method_metadata
        )
        assert response.example_metadata_field == method_metadata["field"]

        # unary stream
        async for response in stub.example_unary_stream(
            example_request, metadata=method_metadata
        ):
            assert response.example_metadata_field == method_metadata["field"]

        # stream unary
        async def request_iterator():
            yield example_request
            yield example_request
            yield example_request

        response = await stub.example_stream_unary(
            request_iterator(), metadata=method_metadata
        )
        assert response.example_metadata_field == method_metadata["field"]

        # stream stream
        async for response in stub.example_stream_stream(
            request_iterator(), metadata=method_metadata
        ):
            assert response.example_metadata_field == method_metadata["field"]
