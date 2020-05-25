from betterproto.tests.output_betterproto.casing_message_field_uppercase.casing_message_field_uppercase import (
    Test,
)


def test_message_casing():
    message = Test()
    assert hasattr(
        message, "upper_camel_case"
    ), "UPPER_CAMEL_CASE attribute is converted to upper_camel_case in python"
