import asyncio
from dataclasses import dataclass
from typing import AsyncIterator

import pytest

import betterproto
from betterproto.grpc.util.async_channel import AsyncChannel


@dataclass
class Message(betterproto.Message):
    body: str = betterproto.string_field(1)


async def to_list(generator: AsyncIterator):
    lis = []
    async for value in generator:
        lis.append(value)
    return lis


@pytest.fixture
def expected_responses():
    return [Message("Hello world 1"), Message("Hello world 2"), Message("Done")]


class ClientStub:
    async def connect(self, requests):
        await asyncio.sleep(0.1)
        async for request in requests:
            await asyncio.sleep(0.1)
            yield request
        await asyncio.sleep(0.1)
        yield Message("Done")


@pytest.fixture
def client():
    # channel = Channel(host='127.0.0.1', port=50051)
    # return ClientStub(channel)
    return ClientStub()


@pytest.mark.asyncio
async def test_from_list_close_automatically(client, expected_responses):
    requests = AsyncChannel(
        [Message(body="Hello world 1"), Message(body="Hello world 2")], close=True
    )

    responses = client.connect(requests)

    assert await to_list(responses) == expected_responses


@pytest.mark.asyncio
async def test_from_list_close_manually_immediately(client, expected_responses):
    requests = AsyncChannel(
        [Message(body="Hello world 1"), Message(body="Hello world 2")], close=False
    )

    requests.close()

    responses = client.connect(requests)

    assert await to_list(responses) == expected_responses


@pytest.mark.asyncio
async def test_from_list_close_manually_after_connect(client, expected_responses):
    requests = AsyncChannel(
        [Message(body="Hello world 1"), Message(body="Hello world 2")], close=False
    )

    responses = client.connect(requests)

    requests.close()

    assert await to_list(responses) == expected_responses


@pytest.mark.asyncio
async def test_send_from_before_connect_and_close_automatically(
    client, expected_responses
):
    requests = AsyncChannel()

    await requests.send_from(
        [Message(body="Hello world 1"), Message(body="Hello world 2")], close=True
    )

    responses = client.connect(requests)

    assert await to_list(responses) == expected_responses


@pytest.mark.asyncio
async def test_send_from_after_connect_and_close_automatically(
    client, expected_responses
):
    requests = AsyncChannel()

    responses = client.connect(requests)

    await requests.send_from(
        [Message(body="Hello world 1"), Message(body="Hello world 2")], close=True
    )

    assert await to_list(responses) == expected_responses


@pytest.mark.asyncio
async def test_send_from_close_manually_immediately(client, expected_responses):
    requests = AsyncChannel()

    responses = client.connect(requests)

    await requests.send_from(
        [Message(body="Hello world 1"), Message(body="Hello world 2")], close=False
    )

    requests.close()

    assert await to_list(responses) == expected_responses
