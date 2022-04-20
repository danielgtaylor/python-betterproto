import tests.output_betterproto.casing_inner_class as casing_inner_class


def test_message_casing_inner_class_name():
    assert hasattr(
        casing_inner_class, "TestInnerClass"
    ), "Inline defined Message is correctly converted to CamelCase"


def test_message_casing_inner_class_attributes():
    message = casing_inner_class.Test()
    assert hasattr(
        message.inner, "old_exp"
    ), "Inline defined Message attribute is snake_case"
