from abc import ABC
from typing import (
    TYPE_CHECKING,
    AsyncIterable,
    AsyncIterator,
    Iterable,
    Mapping,
    Optional,
    Union,
)

import grpc

if TYPE_CHECKING:
    from .._types import (
        T,
        IProtoMessage,
    )

Value = Union[str, bytes]
MetadataLike = Union[Mapping[str, Value], Iterable[tuple[str, Value]]]
MessageSource = Union[Iterable["IProtoMessage"], AsyncIterable["IProtoMessage"]]


class ServiceStub(ABC):

    def __init__(
            self,
            channel: grpc.aio.Channel,
            *,
            timeout: Optional[float] = None,
            metadata: Optional[MetadataLike] = None,
    ) -> None:
        self.channel = channel
        self.timeout = timeout
        self.metadata = metadata

    def _resolve_request_kwargs(
            self,
            timeout: Optional[float],
            metadata: Optional[MetadataLike],
    ):
        return {
            "timeout": self.timeout if timeout is None else timeout,
            "metadata": self.metadata if metadata is None else metadata,
        }

    async def _unary_unary(
            self,
            stub_method: grpc.aio.UnaryUnaryMultiCallable,
            request: "IProtoMessage",
            *,
            timeout: Optional[float] = None,
            metadata: Optional[MetadataLike] = None,
    ) -> "T":
        return await stub_method(
            request,
            **self._resolve_request_kwargs(timeout, metadata),
        )

    async def _unary_stream(
            self,
            stub_method: grpc.aio.UnaryStreamMultiCallable,
            request: "IProtoMessage",
            *,
            timeout: Optional[float] = None,
            metadata: Optional[MetadataLike] = None,
    ) -> AsyncIterator["T"]:
        call = stub_method(
            request,
            **self._resolve_request_kwargs(timeout, metadata),
        )
        async for response in call:
            yield response

    async def _stream_unary(
            self,
            stub_method: grpc.aio.StreamUnaryMultiCallable,
            request_iterator: MessageSource,
            *,
            timeout: Optional[float] = None,
            metadata: Optional[MetadataLike] = None,
    ) -> "T":
        call = stub_method(
            self._wrap_message_iterator(request_iterator),
            **self._resolve_request_kwargs(timeout, metadata),
        )
        return await call

    async def _stream_stream(
            self,
            stub_method: grpc.aio.StreamStreamMultiCallable,
            request_iterator: MessageSource,
            *,
            timeout: Optional[float] = None,
            metadata: Optional[MetadataLike] = None,
    ) -> AsyncIterator["T"]:
        call = stub_method(
            self._wrap_message_iterator(request_iterator),
            **self._resolve_request_kwargs(timeout, metadata),
        )
        async for response in call:
            yield response

    @staticmethod
    def _wrap_message_iterator(
            messages: MessageSource,
    ) -> AsyncIterator["IProtoMessage"]:
        if hasattr(messages, '__aiter__'):
            async def async_wrapper():
                async for message in messages:
                    yield message

            return async_wrapper()
        else:
            async def sync_wrapper():
                for message in messages:
                    yield message

            return sync_wrapper()
