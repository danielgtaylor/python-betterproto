import pytest

import betterproto
from tests.output_betterproto.oneof_enum import (
    Move,
    Signal,
    Test,
)
from tests.util import get_test_case_json_data


def test_which_one_of_returns_enum_with_default_value():
    """
    returns first field when it is enum and set with default value
    """
    message = Test()
    message.from_json(
        get_test_case_json_data("oneof_enum", "oneof_enum-enum-0.json")[0].json
    )

    assert not hasattr(message, "move")
    assert object.__getattribute__(message, "move") == betterproto.PLACEHOLDER
    assert message.signal == Signal.PASS
    assert betterproto.which_one_of(message, "action") == ("signal", Signal.PASS)


def test_which_one_of_returns_enum_with_non_default_value():
    """
    returns first field when it is enum and set with non default value
    """
    message = Test()
    message.from_json(
        get_test_case_json_data("oneof_enum", "oneof_enum-enum-1.json")[0].json
    )
    assert not hasattr(message, "move")
    assert object.__getattribute__(message, "move") == betterproto.PLACEHOLDER
    assert message.signal == Signal.RESIGN
    assert betterproto.which_one_of(message, "action") == ("signal", Signal.RESIGN)


def test_which_one_of_returns_second_field_when_set():
    message = Test()
    message.from_json(get_test_case_json_data("oneof_enum")[0].json)
    assert message.move == Move(x=2, y=3)
    assert not hasattr(message, "signal")
    assert object.__getattribute__(message, "signal") == betterproto.PLACEHOLDER
    assert betterproto.which_one_of(message, "action") == ("move", Move(x=2, y=3))
