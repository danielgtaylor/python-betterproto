from tests.output_betterproto.casing_message_field_uppercase import Test


def test_message_casing():
    message = Test()
    assert hasattr(message, "uppercase"), (
        "UPPERCASE attribute is converted to 'uppercase' in python"
    )
    assert hasattr(message, "uppercase_v2"), (
        "UPPERCASE_V2 attribute is converted to 'uppercase_v2' in python"
    )
    assert hasattr(message, "upper_camel_case"), (
        "UPPER_CAMEL_CASE attribute is converted to upper_camel_case in python"
    )
