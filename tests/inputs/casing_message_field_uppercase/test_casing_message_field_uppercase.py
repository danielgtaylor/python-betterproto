from betterproto import Casing
from tests.output_betterproto.casing_message_field_uppercase import Test


def test_message_casing():
    message = Test()

    assert hasattr(
        message, "uppercase"
    ), "UPPERCASE attribute is converted to 'uppercase' in python"
    assert hasattr(
        message, "uppercase_v2"
    ), "UPPERCASE_V2 attribute is converted to 'uppercase_v2' in python"
    assert hasattr(
        message, "upper_camel_case"
    ), "UPPER_CAMEL_CASE attribute is converted to upper_camel_case in python"


def test_message_casing_roundtrip():
    snake_case_dict = {
        "uppercase": 1,
        "uppercase_v2": 2,
        "upper_camel_case": 3,
        "upper_case_v4": {
            "upper_case_v3": 4,
        },
        "nested_map": {
            "upper_case_v3": 5,
        },
        "nested_dict_map": {
            "foo_key": "bar_value",
        },
        "envelope_camel_case": {
            "upper_case_v3": 6,
        },
    }
    original_case_dict = {
        "UPPERCASE": 1,
        "UPPERCASE_V2": 2,
        "UPPER_CAMEL_CASE": 3,
        "UPPER_CASE_V4": {
            "UPPER_CASE_V3": 4,
        },
        "nestedMap": {
            "UPPER_CASE_V3": 5,
        },
        "nestedDictMap": {
            "foo_key": "bar_value",
        },
        "envelope_CamelCase": {
            "UPPER_CASE_V3": 6,
        },
    }
    camel_case_dict = {
        "uppercase": 1,
        "uppercaseV2": 2,
        "upperCamelCase": 3,
        "upperCaseV4": {
            "upperCaseV3": 4,
        },
        "nestedMap": {
            "upperCaseV3": 5,
        },
        "nestedDictMap": {
            "foo_key": "bar_value",
        },
        "envelopeCamelCase": {
            "upperCaseV3": 6,
        },
    }

    def compare_expected(message: Test):
        message_dict = message.to_dict(casing=None)
        assert message_dict == original_case_dict, message_dict
        message_dict = message.to_dict(casing=Casing.CAMEL)
        assert message_dict == camel_case_dict, message_dict
        message_dict = message.to_dict(casing=Casing.SNAKE)
        assert message_dict == snake_case_dict, message_dict

    compare_expected(Test.from_dict(snake_case_dict))
    compare_expected(Test.from_dict(original_case_dict))
    compare_expected(Test.from_dict(camel_case_dict))
