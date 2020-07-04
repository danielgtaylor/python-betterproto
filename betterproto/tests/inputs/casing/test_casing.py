import betterproto.tests.output_betterproto.casing as casing
from betterproto.tests.output_betterproto.casing import Test


def test_message_attributes():
    message = Test()
    assert hasattr(
        message, "snake_case_message"
    ), "snake_case field name is same in python"
    assert hasattr(message, "camel_case"), "CamelCase field is snake_case in python"
    assert hasattr(message, "uppercase"), "UPPERCASE field is lowercase in python"


def test_message_casing():
    assert hasattr(
        casing, "SnakeCaseMessage"
    ), "snake_case Message name is converted to CamelCase in python"


def test_enum_casing():
    assert hasattr(
        casing, "MyEnum"
    ), "snake_case Enum name is converted to CamelCase in python"
