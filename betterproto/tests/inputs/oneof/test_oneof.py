import betterproto
from betterproto.tests.output_betterproto.oneof.oneof import Test
from betterproto.tests.util import get_test_case_json_data


def test_which_count():
    message = Test()
    message.from_json(get_test_case_json_data("oneof"))
    assert betterproto.which_one_of(message, "foo") == ("count", 100)


def test_which_name():
    message = Test()
    message.from_json(get_test_case_json_data("oneof", "oneof-name.json"))
    assert betterproto.which_one_of(message, "foo") == ("name", "foobar")
