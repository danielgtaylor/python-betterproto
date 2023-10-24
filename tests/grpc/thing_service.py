from typing import Dict

import grpclib
import grpclib.server

from tests.output_betterproto.service import (
    DoThingRequest,
    DoThingResponse,
    GetThingRequest,
    GetThingResponse,
)


class ThingService:
    def __init__(self, test_hook=None):
        # This lets us pass assertions to the servicer ;)
        self.test_hook = test_hook

    async def do_thing(
        self, stream: "grpclib.server.Stream[DoThingRequest, DoThingResponse]"
    ):
        request = await stream.recv_message()
        if self.test_hook is not None:
            self.test_hook(stream)
        await stream.send_message(DoThingResponse([request.name]))

    async def do_many_things(
        self, stream: "grpclib.server.Stream[DoThingRequest, DoThingResponse]"
    ):
        thing_names = [request.name async for request in stream]
        if self.test_hook is not None:
            self.test_hook(stream)
        await stream.send_message(DoThingResponse(thing_names))

    async def get_thing_versions(
        self, stream: "grpclib.server.Stream[GetThingRequest, GetThingResponse]"
    ):
        request = await stream.recv_message()
        if self.test_hook is not None:
            self.test_hook(stream)
        for version_num in range(1, 6):
            await stream.send_message(
                GetThingResponse(name=request.name, version=version_num)
            )

    async def get_different_things(
        self, stream: "grpclib.server.Stream[GetThingRequest, GetThingResponse]"
    ):
        if self.test_hook is not None:
            self.test_hook(stream)
        #  Respond to each input item immediately
        response_num = 0
        async for request in stream:
            response_num += 1
            await stream.send_message(
                GetThingResponse(name=request.name, version=response_num)
            )

    def __mapping__(self) -> Dict[str, "grpclib.const.Handler"]:
        return {
            "/service.Test/DoThing": grpclib.const.Handler(
                self.do_thing,
                grpclib.const.Cardinality.UNARY_UNARY,
                DoThingRequest,
                DoThingResponse,
            ),
            "/service.Test/DoManyThings": grpclib.const.Handler(
                self.do_many_things,
                grpclib.const.Cardinality.STREAM_UNARY,
                DoThingRequest,
                DoThingResponse,
            ),
            "/service.Test/GetThingVersions": grpclib.const.Handler(
                self.get_thing_versions,
                grpclib.const.Cardinality.UNARY_STREAM,
                GetThingRequest,
                GetThingResponse,
            ),
            "/service.Test/GetDifferentThings": grpclib.const.Handler(
                self.get_different_things,
                grpclib.const.Cardinality.STREAM_STREAM,
                GetThingRequest,
                GetThingResponse,
            ),
        }
