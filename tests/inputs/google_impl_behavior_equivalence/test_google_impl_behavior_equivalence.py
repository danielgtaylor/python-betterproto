import pytest
from google.protobuf import json_format

import betterproto
from tests.output_betterproto.google_impl_behavior_equivalence import (
    Empty,
    Foo,
    Request,
    Test,
)
from tests.output_reference.google_impl_behavior_equivalence.google_impl_behavior_equivalence_pb2 import (
    Empty as ReferenceEmpty,
    Foo as ReferenceFoo,
    Request as ReferenceRequest,
    Test as ReferenceTest,
)


def test_oneof_serializes_similar_to_google_oneof():
    tests = [
        (Test(string="abc"), ReferenceTest(string="abc")),
        (Test(integer=2), ReferenceTest(integer=2)),
        (Test(foo=Foo(bar=1)), ReferenceTest(foo=ReferenceFoo(bar=1))),
        # Default values should also behave the same within oneofs
        (Test(string=""), ReferenceTest(string="")),
        (Test(integer=0), ReferenceTest(integer=0)),
        (Test(foo=Foo(bar=0)), ReferenceTest(foo=ReferenceFoo(bar=0))),
    ]
    for message, message_reference in tests:
        # NOTE: As of July 2020, MessageToJson inserts newlines in the output string so,
        # just compare dicts
        assert message.to_dict() == json_format.MessageToDict(message_reference)


def test_bytes_are_the_same_for_oneof():
    message = Test(string="")
    message_reference = ReferenceTest(string="")

    message_bytes = bytes(message)
    message_reference_bytes = message_reference.SerializeToString()

    assert message_bytes == message_reference_bytes

    message2 = Test().parse(message_reference_bytes)
    message_reference2 = ReferenceTest()
    message_reference2.ParseFromString(message_reference_bytes)

    assert message == message2
    assert message_reference == message_reference2

    # None of these fields were explicitly set BUT they should not actually be null
    # themselves
    assert not hasattr(message, "foo")
    assert object.__getattribute__(message, "foo") == betterproto.PLACEHOLDER
    assert not hasattr(message2, "foo")
    assert object.__getattribute__(message2, "foo") == betterproto.PLACEHOLDER

    assert isinstance(message_reference.foo, ReferenceFoo)
    assert isinstance(message_reference2.foo, ReferenceFoo)


def test_empty_message_field():
    message = Request()
    reference_message = ReferenceRequest()

    message.foo = Empty()
    reference_message.foo.CopyFrom(ReferenceEmpty())

    assert betterproto.serialized_on_wire(message.foo)
    assert reference_message.HasField("foo")

    assert bytes(message) == reference_message.SerializeToString()
