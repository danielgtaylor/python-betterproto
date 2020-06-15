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

    pass


class ChannelDone(Exception):
    """
    An exception raised on an attempt to send recieve from a channel that is both closed
    and empty.
    """

    pass


class AsyncChannel(AsyncIterable[T]):
    """
    A buffered async channel for sending items between coroutines with FIFO semantics.

    This makes decoupled bidirection steaming gRPC requests easy if used like:

    .. code-block:: python
        client = GeneratedStub(grpclib_chan)
        # The channel can be initialised with items to send immediately
        request_chan = AsyncChannel([ReqestObject(...), ReqestObject(...)])
        async for response in client.rpc_call(request_chan):
            # The response iterator will remain active until the connection is closed
            ...
            # More items can be sent at any time
            await request_chan.send(ReqestObject(...))
            ...
            # The channel must be closed to complete the gRPC connection
            request_chan.close()

    Items can be sent through the channel by either:
    - providing an iterable to the constructor
    - providing an iterable to the send_from method
    - passing them to the send method one at a time

    Items can be recieved from the channel by either:
    - iterating over the channel with a for loop to get all items
    - calling the recieve method to get one item at a time

    If the channel is empty then recievers will wait until either an item appears or the
    channel is closed.

    Once the channel is closed then subsequent attempt to send through the channel will
    fail with a ChannelClosed exception.

    When th channel is closed and empty then it is done, and further attempts to recieve
    from it will fail with a ChannelDone exception

    If multiple coroutines recieve from the channel concurrently, each item sent will be
    recieved by only one of the recievers.

    :param source:
        An optional iterable will items that should be sent through the channel
        immediately.
    :param buffer_limit:
        Limit the number of items that can be buffered in the channel, A value less than
        1 implies no limit. If the channel is full then attempts to send more items will
        result in the sender waiting until an item is recieved from the channel.
    :param close:
        If set to True then the channel will automatically close after exhausting source
        or immediately if no source is provided.
    """

    def __init__(
        self, *, buffer_limit: int = 0, close: bool = False,
    ):
        self._queue: asyncio.Queue[Union[T, object]] = asyncio.Queue(buffer_limit)
        self._closed = False
        self._waiting_recievers: int = 0
        # Track whether flush has been invoked so it can only happen once
        self._flushed = False

    def __aiter__(self) -> AsyncIterator[T]:
        return self

    async def __anext__(self) -> T:
        if self.done():
            raise StopAsyncIteration
        self._waiting_recievers += 1
        try:
            result = await self._queue.get()
            if result is self.__flush:
                raise StopAsyncIteration
            return result
        finally:
            self._waiting_recievers -= 1
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
        which case any further attempts to recieve an item from this channel will raise
        a ChannelDone exception.
        """
        # After close the channel is not yet done until there is at least one waiting
        # reciever per enqueued item.
        return self._closed and self._queue.qsize() <= self._waiting_recievers

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

    async def recieve(self) -> Optional[T]:
        """
        Returns the next item from this channel when it becomes available,
        or None if the channel is closed before another item is sent.
        :return: An item from the channel
        """
        if self.done():
            raise ChannelDone("Cannot recieve from a closed channel")
        self._waiting_recievers += 1
        try:
            result = await self._queue.get()
            if result is self.__flush:
                return None
            return result
        finally:
            self._waiting_recievers -= 1
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
            deadlocked_recievers = max(0, self._waiting_recievers - self._queue.qsize())
            for _ in range(deadlocked_recievers):
                await self._queue.put(self.__flush)

    # A special signal object for flushing the queue when the channel is closed
    __flush = object()
