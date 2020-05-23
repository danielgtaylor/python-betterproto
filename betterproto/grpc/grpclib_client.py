from abc import ABC
import grpclib.const
from typing import (
    AsyncGenerator,
    AsyncIterator,
    Collection,
    Iterator,
    Mapping,
    Optional,
    Tuple,
    TYPE_CHECKING,
    Type,
    Union,
)
from .._types import ST, T

if TYPE_CHECKING:
    from grpclib._protocols import IProtoMessage
    from grpclib.client import Channel
    from grpclib.metadata import Deadline


_Value = Union[str, bytes]
_MetadataLike = Union[Mapping[str, _Value], Collection[Tuple[str, _Value]]]


class ServiceStub(ABC):
    """
    Base class for async gRPC service stubs.
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
        request: "IProtoMessage",
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
        request: "IProtoMessage",
        response_type: Type[T],
        *,
        timeout: Optional[float] = None,
        deadline: Optional["Deadline"] = None,
        metadata: Optional[_MetadataLike] = None,
    ) -> AsyncGenerator[T, None]:
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
        request_iterator: Iterator["IProtoMessage"],
        request_type: Type[ST],
        response_type: Type[T],
    ) -> T:
        """Make a stream request and return the response."""
        async with self.channel.request(
            route, grpclib.const.Cardinality.STREAM_UNARY, request_type, response_type
        ) as stream:
            for message in request_iterator:
                await stream.send_message(message)
            await stream.send_request(end=True)
            response = await stream.recv_message()
            assert response is not None
            return response

    async def _stream_stream(
        self,
        route: str,
        request_iterator: Iterator["IProtoMessage"],
        request_type: Type[ST],
        response_type: Type[T],
    ) -> AsyncGenerator[T, None]:
        """Make a stream request and return the stream response iterator."""
        async with self.channel.request(
            route, grpclib.const.Cardinality.STREAM_STREAM, request_type, response_type
        ) as stream:
            for message in request_iterator:
                await stream.send_message(message)
            await stream.send_request(end=True)
            async for message in stream:
                yield message
