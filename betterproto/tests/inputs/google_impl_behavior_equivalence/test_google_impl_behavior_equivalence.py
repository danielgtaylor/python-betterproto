import pytest

from google.protobuf import json_format
import betterproto
from betterproto.tests.output_betterproto.google_impl_behavior_equivalence import (
    OneOfTest,
    Foo,
)
from betterproto.tests.output_reference.google_impl_behavior_equivalence.google_impl_behavior_equivalence_pb2 import (
    OneOfTest as ReferenceOneOfTest,
    Foo as ReferenceFoo,
)


def test_oneof_serializes_similar_to_google_oneof():

    tests = [
        (OneOfTest(string="abc"), ReferenceOneOfTest(string="abc")),
        (OneOfTest(integer=2), ReferenceOneOfTest(integer=2)),
        (OneOfTest(foo=Foo(bar=1)), ReferenceOneOfTest(foo=ReferenceFoo(bar=1))),
        # Default values should also behave the same within oneofs
        (OneOfTest(string=""), ReferenceOneOfTest(string="")),
        (OneOfTest(integer=0), ReferenceOneOfTest(integer=0)),
        (OneOfTest(foo=Foo(bar=0)), ReferenceOneOfTest(foo=ReferenceFoo(bar=0))),
    ]
    for message, message_reference in tests:
        # NOTE: As of July 2020, MessageToJson inserts newlines in the output string so,
        # just compare dicts
        assert message.to_dict() == json_format.MessageToDict(message_reference)


def test_bytes_are_the_same_for_oneof():

    message = OneOfTest(string="")
    message_reference = ReferenceOneOfTest(string="")

    message_bytes = bytes(message)
    message_reference_bytes = message_reference.SerializeToString()

    assert message_bytes == message_reference_bytes

    message2 = OneOfTest().parse(message_reference_bytes)
    message_reference2 = ReferenceOneOfTest()
    message_reference2.ParseFromString(message_reference_bytes)

    assert message == message2
    assert message_reference == message_reference2

    # None of these fields were explicitly set BUT they should not actually be null
    # themselves
    assert isinstance(message.foo, Foo)
    assert isinstance(message2.foo, Foo)

    assert isinstance(message_reference.foo, ReferenceFoo)
    assert isinstance(message_reference2.foo, ReferenceFoo)
