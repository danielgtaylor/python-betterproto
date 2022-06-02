from tests.output_betterproto.googletypes_value import Test
from tests.util import get_test_case_json_data


def test_value():
    message = Test()
    message.from_json(get_test_case_json_data("googletypes_value")[0].json)
    assert message.value1 == "hello world"
    assert message.value4 is None
