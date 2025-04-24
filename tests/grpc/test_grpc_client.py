""" Testing the sync version of the client stubs.

This is not testing the lower level grpc calls, but rather the generated client stubs.
So instead of creating a real service and a real grpc channel,
we are going to mock the channel and simply test the client.

If we wanted to test without mocking we would need to use all the machinery here:
https://github.com/grpc/grpc/blob/master/src/python/grpcio_tests/tests/testing/_client_test.py

"""

import re
from sys import version
from tests.output_betterproto.service import (
    DoThingRequest,
    DoThingResponse,
    GetThingRequest,
    GetThingResponse,
    TestSyncStub as ThingServiceClient,
)


class ChannelMock:
    """channel.unary_unary(
            "/service.Test/DoThing",
            DoThingRequest.SerializeToString,
            DoThingResponse.FromString,
        )(do_thing_request)
        the method calls the serialize, then use the deserialize and returns the response"""
    
    def unary_unary(self, route, request_serializer, response_deserializer):
        """mock the unary_unary call"""
        def _unary_unary(req):
            return response_deserializer(request_serializer(req))
        return _unary_unary
    
    def stream_unary(self, route, request_serializer, response_deserializer):
        """mock the stream_unary call"""
        def _stream_unary(req):
            return response_deserializer(request_serializer(next(req)))
        return _stream_unary
    
    def stream_stream(self, route, request_serializer, response_deserializer):
        """mock the stream_stream call"""
        def _stream_stream(req):
            return (response_deserializer(request_serializer(r)) for r in req)
        return _stream_stream
    
    def unary_stream(self, route, request_serializer, response_deserializer):
        """mock the unary_stream call"""    
        def _unary_stream(req):
            return iter([response_deserializer(request_serializer(req))]*6)
        return _unary_stream
    

def test_do_thing_call(mocker):
    """mock the channel and test the client stub"""
    client = ThingServiceClient(channel=ChannelMock())
    response = client.do_thing(DoThingRequest(name="clean room"))
    assert response.names == ["clean room"]

def test_do_many_things_call(mocker):
    """mock the channel and test the client stub"""
    client = ThingServiceClient(channel=ChannelMock())
    response = client.do_many_things(iter([
        DoThingRequest(name="only"),
        DoThingRequest(name="room")]))
    assert response == DoThingResponse(names=["only"]) #protobuf is stunning

def test_get_thing_versions_call(mocker):
    """mock the channel and test the client stub"""
    client = ThingServiceClient(channel=ChannelMock())
    response = client.get_thing_versions(GetThingRequest(name="extra"))
    response = list(response)
    assert response == [GetThingResponse(name="extra")]*6

def test_get_different_things_call(mocker):
    """mock the channel and test the client stub"""
    client = ThingServiceClient(channel=ChannelMock())
    response = client.get_different_things([
        GetThingRequest(name="apple"),
        GetThingRequest(name="orange")])
    response = list(response)
    assert response == [GetThingResponse(name="apple"), GetThingResponse(name="orange")]
