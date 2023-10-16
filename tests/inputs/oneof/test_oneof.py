import pytest

import betterproto
from tests.output_betterproto.oneof import (
    MixedDrink,
    Test,
)
from tests.output_betterproto_pydantic.oneof import Test as TestPyd
from tests.util import get_test_case_json_data


def test_which_count():
    message = Test()
    message.from_json(get_test_case_json_data("oneof")[0].json)
    assert betterproto.which_one_of(message, "foo") == ("pitied", 100)


def test_which_name():
    message = Test()
    message.from_json(get_test_case_json_data("oneof", "oneof_name.json")[0].json)
    assert betterproto.which_one_of(message, "foo") == ("pitier", "Mr. T")


def test_which_count_pyd():
    message = TestPyd(pitier="Mr. T", just_a_regular_field=2, bar_name="a_bar")
    assert betterproto.which_one_of(message, "foo") == ("pitier", "Mr. T")


def test_oneof_constructor_assign():
    message = Test(mixed_drink=MixedDrink(shots=42))
    field, value = betterproto.which_one_of(message, "bar")
    assert field == "mixed_drink"
    assert value.shots == 42


# Issue #305:
@pytest.mark.xfail
def test_oneof_nested_assign():
    message = Test()
    message.mixed_drink.shots = 42
    field, value = betterproto.which_one_of(message, "bar")
    assert field == "mixed_drink"
    assert value.shots == 42
