import pytest

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

    assert message.move == Move(
        x=0, y=0
    )  # Proto3 will default this as there is no null
    assert message.signal == Signal.PASS
    assert message.which_one_of("action") == ("signal", Signal.PASS)


def test_which_one_of_returns_enum_with_non_default_value():
    """
    returns first field when it is enum and set with non default value
    """
    message = Test()
    message.from_json(
        get_test_case_json_data("oneof_enum", "oneof_enum-enum-1.json")[0].json
    )
    assert message.move == Move(
        x=0, y=0
    )  # Proto3 will default this as there is no null
    assert message.signal == Signal.RESIGN
    assert message.which_one_of("action") == ("signal", Signal.RESIGN)


def test_which_one_of_returns_second_field_when_set():
    message = Test()
    message.from_json(get_test_case_json_data("oneof_enum")[0].json)
    assert message.move == Move(x=2, y=3)
    assert message.signal == Signal.PASS
    assert message.which_one_of("action") == ("move", Move(x=2, y=3))
