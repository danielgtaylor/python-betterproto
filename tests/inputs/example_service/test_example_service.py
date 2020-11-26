from typing import AsyncIterator, AsyncIterable

import pytest
from grpclib.testing import ChannelFor

from tests.output_betterproto.example_service.example_service import (
    TestBase,
    TestStub,
    ExampleRequest,
    ExampleResponse,
)


class ExampleService(TestBase):
    async def example_unary_unary(
        self, example_string: str, example_integer: int
    ) -> "ExampleResponse":
        return ExampleResponse(
            example_string=example_string,
            example_integer=example_integer,
        )

    async def example_unary_stream(
        self, example_string: str, example_integer: int
    ) -> AsyncIterator["ExampleResponse"]:
        response = ExampleResponse(
            example_string=example_string,
            example_integer=example_integer,
        )
        yield response
        yield response
        yield response

    async def example_stream_unary(
        self, example_request_iterator: AsyncIterable["ExampleRequest"]
    ) -> "ExampleResponse":
        async for example_request in example_request_iterator:
            return ExampleResponse(
                example_string=example_request.example_string,
                example_integer=example_request.example_integer,
            )

    async def example_stream_stream(
        self, example_request_iterator: AsyncIterable["ExampleRequest"]
    ) -> AsyncIterator["ExampleResponse"]:
        async for example_request in example_request_iterator:
            yield ExampleResponse(
                example_string=example_request.example_string,
                example_integer=example_request.example_integer,
            )


@pytest.mark.asyncio
async def test_calls_with_different_cardinalities():
    test_string = "test string"
    test_int = 42

    async with ChannelFor([ExampleService()]) as channel:
        stub = TestStub(channel)

        # unary unary
        response = await stub.example_unary_unary(
            example_string="test string",
            example_integer=42,
        )
        assert response.example_string == test_string
        assert response.example_integer == test_int

        # unary stream
        async for response in stub.example_unary_stream(
            example_string="test string",
            example_integer=42,
        ):
            assert response.example_string == test_string
            assert response.example_integer == test_int

        # stream unary
        request = ExampleRequest(
            example_string=test_string,
            example_integer=42,
        )

        async def request_iterator():
            yield request
            yield request
            yield request

        response = await stub.example_stream_unary(request_iterator())
        assert response.example_string == test_string
        assert response.example_integer == test_int

        # stream stream
        async for response in stub.example_stream_stream(request_iterator()):
            assert response.example_string == test_string
            assert response.example_integer == test_int
