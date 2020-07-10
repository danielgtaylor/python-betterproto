from typing import List

from grpclib.client import Channel


class MockChannel(Channel):
    # noinspection PyMissingConstructor
    def __init__(self, responses=None) -> None:
        self.responses = responses if responses else []
        self.requests = []
        self._loop = None

    def request(self, route, cardinality, request, response_type, **kwargs):
        self.requests.append(
            {
                "route": route,
                "cardinality": cardinality,
                "request": request,
                "response_type": response_type,
            }
        )
        return MockStream(self.responses)


class MockStream:
    def __init__(self, responses: List) -> None:
        super().__init__()
        self.responses = responses

    async def recv_message(self):
        return self.responses.pop(0)

    async def send_message(self, *args, **kwargs):
        pass

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return True

    async def __aenter__(self):
        return self
