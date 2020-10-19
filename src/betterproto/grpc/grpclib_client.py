import asyncio
from abc import ABC
from typing import (
    TYPE_CHECKING,
    AsyncIterable,
    AsyncIterator,
    Collection,
    Iterable,
    Mapping,
    Optional,
    Tuple,
    Type,
    Union,
)

import grpclib.const

from .._types import ST, T

if TYPE_CHECKING:
    from grpclib.client import Channel
    from grpclib.metadata import Deadline


_Value = Union[str, bytes]
_MetadataLike = Union[Mapping[str, _Value], Collection[Tuple[str, _Value]]]
_MessageLike = Union[T, ST]
_MessageSource = Union[Iterable[ST], AsyncIterable[ST]]


class ServiceStub(ABC):
    """
    Base class for async gRPC clients.
    """

    def __init__(
        self,
        channel: "Channel",
        *,
        timeout: Optional[float] = None,
        deadline: Optional["Deadline"] = None,
        metadata: Optional[_MetadataLike] = None,
    ) -> None:
        self.channel = channel
        self.timeout = timeout
        self.deadline = deadline
        self.metadata = metadata

    def __resolve_request_kwargs(
        self,
        timeout: Optional[float],
        deadline: Optional["Deadline"],
        metadata: Optional[_MetadataLike],
    ):
        return {
            "timeout": self.timeout if timeout is None else timeout,
            "deadline": self.deadline if deadline is None else deadline,
            "metadata": self.metadata if metadata is None else metadata,
        }

    async def _unary_unary(
        self,
        route: str,
        request: _MessageLike,
        response_type: Type[T],
        *,
        timeout: Optional[float] = None,
        deadline: Optional["Deadline"] = None,
        metadata: Optional[_MetadataLike] = None,
    ) -> T:
        """Make a unary request and return the response."""
        async with self.channel.request(
            route,
            grpclib.const.Cardinality.UNARY_UNARY,
            type(request),
            response_type,
            **self.__resolve_request_kwargs(timeout, deadline, metadata),
        ) as stream:
            await stream.send_message(request, end=True)
            response = await stream.recv_message()
        assert response is not None
        return response

    async def _unary_stream(
        self,
        route: str,
        request: _MessageLike,
        response_type: Type[T],
        *,
        timeout: Optional[float] = None,
        deadline: Optional["Deadline"] = None,
        metadata: Optional[_MetadataLike] = None,
    ) -> AsyncIterator[T]:
        """Make a unary request and return the stream response iterator."""
        async with self.channel.request(
            route,
            grpclib.const.Cardinality.UNARY_STREAM,
            type(request),
            response_type,
            **self.__resolve_request_kwargs(timeout, deadline, metadata),
        ) as stream:
            await stream.send_message(request, end=True)
            async for message in stream:
                yield message

    async def _stream_unary(
        self,
        route: str,
        request_iterator: _MessageSource,
        request_type: Type[ST],
        response_type: Type[T],
        *,
        timeout: Optional[float] = None,
        deadline: Optional["Deadline"] = None,
        metadata: Optional[_MetadataLike] = None,
    ) -> T:
        """Make a stream request and return the response."""
        async with self.channel.request(
            route,
            grpclib.const.Cardinality.STREAM_UNARY,
            request_type,
            response_type,
            **self.__resolve_request_kwargs(timeout, deadline, metadata),
        ) as stream:
            await self._send_messages(stream, request_iterator)
            response = await stream.recv_message()
        assert response is not None
        return response

    async def _stream_stream(
        self,
        route: str,
        request_iterator: _MessageSource,
        request_type: Type[ST],
        response_type: Type[T],
        *,
        timeout: Optional[float] = None,
        deadline: Optional["Deadline"] = None,
        metadata: Optional[_MetadataLike] = None,
    ) -> AsyncIterator[T]:
        """
        Make a stream request and return an AsyncIterator to iterate over response
        messages.
        """
        async with self.channel.request(
            route,
            grpclib.const.Cardinality.STREAM_STREAM,
            request_type,
            response_type,
            **self.__resolve_request_kwargs(timeout, deadline, metadata),
        ) as stream:
            await stream.send_request()
            sending_task = asyncio.ensure_future(
                self._send_messages(stream, request_iterator)
            )
            try:
                async for response in stream:
                    yield response
            except:
                sending_task.cancel()
                raise

    @staticmethod
    async def _send_messages(stream, messages: _MessageSource):
        if isinstance(messages, AsyncIterable):
            async for message in messages:
                await stream.send_message(message)
        else:
            for message in messages:
                await stream.send_message(message)
        await stream.end()
