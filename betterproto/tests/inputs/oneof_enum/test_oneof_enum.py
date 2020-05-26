import pytest

import betterproto
from betterproto.tests.output_betterproto.oneof_enum.oneof_enum import (
    Move,
    Signal,
    Test,
)
from betterproto.tests.util import get_test_case_json_data


@pytest.mark.xfail
def test_which_one_of_returns_enum_with_default_value():
    """
    returns first field when it is enum and set with default value
    """
    message = Test()
    message.from_json(get_test_case_json_data("oneof_enum", "oneof_enum-enum-0.json"))
    assert message.move is None
    assert message.signal == Signal.PASS
    assert betterproto.which_one_of(message, "action") == ("signal", Signal.PASS)


@pytest.mark.xfail
def test_which_one_of_returns_enum_with_non_default_value():
    """
    returns first field when it is enum and set with non default value
    """
    message = Test()
    message.from_json(get_test_case_json_data("oneof_enum", "oneof_enum-enum-1.json"))
    assert message.move is None
    assert message.signal == Signal.PASS
    assert betterproto.which_one_of(message, "action") == ("signal", Signal.RESIGN)


@pytest.mark.xfail
def test_which_one_of_returns_second_field_when_set():
    message = Test()
    message.from_json(get_test_case_json_data("oneof_enum"))
    assert message.move == Move(x=2, y=3)
    assert message.signal == 0
    assert betterproto.which_one_of(message, "action") == ("move", Move(x=2, y=3))
