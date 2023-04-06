import asyncio
from typing import (
    AsyncIterable,
    AsyncIterator,
    Iterable,
    Optional,
    TypeVar,
    Union,
)


T = TypeVar("T")


class ChannelClosed(Exception):
    """
    An exception raised on an attempt to send through a closed channel
    """


class ChannelDone(Exception):
    """
    An exception raised on an attempt to send receive from a channel that is both closed
    and empty.
    """


class AsyncChannel(AsyncIterable[T]):
    """
    A buffered async channel for sending items between coroutines with FIFO ordering.

    This makes decoupled bidirectional steaming gRPC requests easy if used like:

    .. code-block:: python
        client = GeneratedStub(grpclib_chan)
        request_channel = await AsyncChannel()
        # We can start be sending all the requests we already have
        await request_channel.send_from([RequestObject(...), RequestObject(...)])
        async for response in client.rpc_call(request_channel):
            # The response iterator will remain active until the connection is closed
            ...
            # More items can be sent at any time
            await request_channel.send(RequestObject(...))
            ...
            # The channel must be closed to complete the gRPC connection
            request_channel.close()

    Items can be sent through the channel by either:
    - providing an iterable to the send_from method
    - passing them to the send method one at a time

    Items can be received from the channel by either:
    - iterating over the channel with a for loop to get all items
    - calling the receive method to get one item at a time

    If the channel is empty then receivers will wait until either an item appears or the
    channel is closed.

    Once the channel is closed then subsequent attempt to send through the channel will
    fail with a ChannelClosed exception.

    When th channel is closed and empty then it is done, and further attempts to receive
    from it will fail with a ChannelDone exception

    If multiple coroutines receive from the channel concurrently, each item sent will be
    received by only one of the receivers.

    :param source:
        An optional iterable will items that should be sent through the channel
        immediately.
    :param buffer_limit:
        Limit the number of items that can be buffered in the channel, A value less than
        1 implies no limit. If the channel is full then attempts to send more items will
        result in the sender waiting until an item is received from the channel.
    :param close:
        If set to True then the channel will automatically close after exhausting source
        or immediately if no source is provided.
    """

    def __init__(self, *, buffer_limit: int = 0, close: bool = False):
        self._queue: asyncio.Queue[T] = asyncio.Queue(buffer_limit)
        self._closed = False
        self._waiting_receivers: int = 0
        # Track whether flush has been invoked so it can only happen once
        self._flushed = False

    def __aiter__(self) -> AsyncIterator[T]:
        return self

    async def __anext__(self) -> T:
        if self.done():
            raise StopAsyncIteration
        self._waiting_receivers += 1
        try:
            result = await self._queue.get()
            if result is self.__flush:
                raise StopAsyncIteration
            return result
        finally:
            self._waiting_receivers -= 1
            self._queue.task_done()

    def closed(self) -> bool:
        """
        Returns True if this channel is closed and no-longer accepting new items
        """
        return self._closed

    def done(self) -> bool:
        """
        Check if this channel is done.

        :return: True if this channel is closed and and has been drained of items in
        which case any further attempts to receive an item from this channel will raise
        a ChannelDone exception.
        """
        # After close the channel is not yet done until there is at least one waiting
        # receiver per enqueued item.
        return self._closed and self._queue.qsize() <= self._waiting_receivers

    async def send_from(
        self, source: Union[Iterable[T], AsyncIterable[T]], close: bool = False
    ) -> "AsyncChannel[T]":
        """
        Iterates the given [Async]Iterable and sends all the resulting items.
        If close is set to True then subsequent send calls will be rejected with a
        ChannelClosed exception.
        :param source: an iterable of items to send
        :param close:
            if True then the channel will be closed after the source has been exhausted

        """
        if self._closed:
            raise ChannelClosed("Cannot send through a closed channel")
        if isinstance(source, AsyncIterable):
            async for item in source:
                await self._queue.put(item)
        else:
            for item in source:
                await self._queue.put(item)
        if close:
            # Complete the closing process
            self.close()
        return self

    async def send(self, item: T) -> "AsyncChannel[T]":
        """
        Send a single item over this channel.
        :param item: The item to send
        """
        if self._closed:
            raise ChannelClosed("Cannot send through a closed channel")
        await self._queue.put(item)
        return self

    async def receive(self) -> Optional[T]:
        """
        Returns the next item from this channel when it becomes available,
        or None if the channel is closed before another item is sent.
        :return: An item from the channel
        """
        if self.done():
            raise ChannelDone("Cannot receive from a closed channel")
        self._waiting_receivers += 1
        try:
            result = await self._queue.get()
            if result is self.__flush:
                return None
            return result
        finally:
            self._waiting_receivers -= 1
            self._queue.task_done()

    def close(self):
        """
        Close this channel to new items
        """
        self._closed = True
        asyncio.ensure_future(self._flush_queue())

    async def _flush_queue(self):
        """
        To be called after the channel is closed. Pushes a number of self.__flush
        objects to the queue to ensure no waiting consumers get deadlocked.
        """
        if not self._flushed:
            self._flushed = True
            deadlocked_receivers = max(0, self._waiting_receivers - self._queue.qsize())
            for _ in range(deadlocked_receivers):
                await self._queue.put(self.__flush)

    # A special signal object for flushing the queue when the channel is closed
    __flush = object()
