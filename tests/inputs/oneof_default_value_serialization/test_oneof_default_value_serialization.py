import datetime

import pytest

import bananaproto
from tests.output_bananaproto.oneof_default_value_serialization import (
    Message,
    NestedMessage,
    Test,
)


def assert_round_trip_serialization_works(message: Test) -> None:
    assert bananaproto.which_one_of(message, "value_type") == bananaproto.which_one_of(
        Test().from_json(message.to_json()), "value_type"
    )


def test_oneof_default_value_serialization_works_for_all_values():
    """
    Serialization from message with oneof set to default -> JSON -> message should keep
    default value field intact.
    """

    test_cases = [
        Test(bool_value=False),
        Test(int64_value=0),
        Test(
            timestamp_value=datetime.datetime(
                year=1970,
                month=1,
                day=1,
                hour=0,
                minute=0,
                tzinfo=datetime.timezone.utc,
            )
        ),
        Test(duration_value=datetime.timedelta(0)),
        Test(wrapped_message_value=Message(value=0)),
        # NOTE: Do NOT use bananaproto.BoolValue here, it will cause JSON serialization
        # errors.
        # TODO: Do we want to allow use of BoolValue directly within a wrapped field or
        # should we simply hard fail here?
        Test(wrapped_bool_value=False),
    ]
    for message in test_cases:
        assert_round_trip_serialization_works(message)


def test_oneof_no_default_values_passed():
    message = Test()
    assert (
        bananaproto.which_one_of(message, "value_type")
        == bananaproto.which_one_of(Test().from_json(message.to_json()), "value_type")
        == ("", None)
    )


def test_oneof_nested_oneof_messages_are_serialized_with_defaults():
    """
    Nested messages with oneofs should also be handled
    """
    message = Test(
        wrapped_nested_message_value=NestedMessage(
            id=0, wrapped_message_value=Message(value=0)
        )
    )
    assert (
        bananaproto.which_one_of(message, "value_type")
        == bananaproto.which_one_of(Test().from_json(message.to_json()), "value_type")
        == (
            "wrapped_nested_message_value",
            NestedMessage(id=0, wrapped_message_value=Message(value=0)),
        )
    )
