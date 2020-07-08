import pytest

import betterproto
from betterproto.tests.output_betterproto.oneof_default_value_serialization import Test


def test_oneof_default_value_serialization():
    """
    Serialization from message with oneof set to default -> JSON -> message should keep
    default value field intact.
    """
    message = Test(bool_value=False)
    message2 = Test().from_json(message.to_json())

    assert betterproto.which_one_of(message, "value_type") == betterproto.which_one_of(
        message2, "value_type"
    )

    message.int64_value = 0
    message2 = Test().from_json(message.to_json())
    assert betterproto.which_one_of(message, "value_type") == betterproto.which_one_of(
        message2, "value_type"
    )


def test_oneof_no_default_values_passed():
    """
    Serialization from message with oneof set to default -> JSON -> message should keep
    default value field intact.
    """
    message = Test()
    message2 = Test().from_json(message.to_json())

    assert (
        betterproto.which_one_of(message, "value_type")
        == betterproto.which_one_of(message2, "value_type")
        == ("", None)
    )
