from typing import Iterator

from tests.output_betterproto.service_grpcio import (
    DoThingRequest,
    DoThingResponse,
    GetThingRequest,
    GetThingResponse,
)


class ThingServiceGrpcio:

    def __init__(self, test_hook=None):
        self.test_hook = test_hook

    def do_thing(self, request: DoThingRequest, context=None) -> DoThingResponse:
        if self.test_hook is not None:
            self.test_hook(context)
        return DoThingResponse(names=[request.name])

    def do_many_things(self, request_iterator: Iterator[DoThingRequest], context=None) -> DoThingResponse:
        thing_names = [request.name for request in request_iterator]
        if self.test_hook is not None:
            self.test_hook(context)
        return DoThingResponse(names=thing_names)

    def get_thing_versions(self, request: GetThingRequest, context=None) -> Iterator[GetThingResponse]:
        if self.test_hook is not None:
            self.test_hook(context)
        for version_num in range(5, 0, -1):  # 5, 4, 3, 2, 1
            yield GetThingResponse(name=request.name, version=version_num)

    def get_different_things(self, request_iterator: Iterator[GetThingRequest], context=None) -> Iterator[GetThingResponse]:
        if self.test_hook is not None:
            self.test_hook(context)
        version = 1
        for request in request_iterator:
            yield GetThingResponse(name=request.name, version=version)
            version += 1


class GrpcioTestChannel:
    def __init__(self, service: ThingServiceGrpcio):
        self.service = service

    def route_call(self, method: str, request, context=None):
        if method == "/service.Test/DoThing":
            return self.service.do_thing(request, context)
        elif method == "/service.Test/DoManyThings":
            return self.service.do_many_things(request, context)
        elif method == "/service.Test/GetThingVersions":
            return self.service.get_thing_versions(request, context)
        elif method == "/service.Test/GetDifferentThings":
            return self.service.get_different_things(request, context)
        else:
            raise NotImplementedError(f"Method {method} not implemented")


def create_test_channel(service_instance: ThingServiceGrpcio):
    return GrpcioTestChannel(service_instance)
