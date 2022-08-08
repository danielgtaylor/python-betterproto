import betterproto
from tests.output_betterproto.oneof import Test
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
