import betterproto
from tests.output_betterproto.oneof_struct import Test
from tests.util import get_test_case_json_data


def test_which_name():
    message = Test()
    message.from_json(
        get_test_case_json_data("oneof_struct", "oneof_struct.json")[0].json
    )
    assert betterproto.which_one_of(message, "foo")[0] == "bar"
