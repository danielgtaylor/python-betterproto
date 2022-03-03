from tests.output_betterproto.oneof import Test
from tests.util import get_test_case_json_data


def test_which_count():
    message = Test()
    message.from_json(get_test_case_json_data("oneof")[0].json)
    assert message.which_one_of("foo") == ("pitied", 100)


def test_which_name():
    message = Test()
    message.from_json(get_test_case_json_data("oneof", "oneof_name.json")[0].json)
    assert message.which_one_of("foo") == ("pitier", "Mr. T")
