from abc import ABC
from collections import AsyncIterable
from typing import Callable, Any, Dict

import grpclib
import grpclib.server


class ServiceBase(ABC):
    """
    Base class for async gRPC servers.
    """

    async def _call_rpc_handler_server_stream(
        self,
        handler: Callable,
        stream: grpclib.server.Stream,
        request_kwargs: Dict[str, Any],
    ) -> None:

        response_iter = handler(**request_kwargs)
        # check if response is actually an AsyncIterator
        # this might be false if the method just returns without
        # yielding at least once
        # in that case, we just interpret it as an empty iterator
        if isinstance(response_iter, AsyncIterable):
            async for response_message in response_iter:
                await stream.send_message(response_message)
        else:
            response_iter.close()
