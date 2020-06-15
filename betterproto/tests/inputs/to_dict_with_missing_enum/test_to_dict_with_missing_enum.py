from betterproto.tests.output_betterproto.to_dict_with_missing_enum.to_dict_with_missing_enum import TestMessage, TestMessageMyEnum


def test_message_attributes():
    assert TestMessage(x=TestMessageMyEnum.ONE).to_dict()['x'] == "ONE", "MyEnum.ONE is not serialized to 'ONE'"
    assert TestMessage(x=TestMessageMyEnum.THREE).to_dict()['x'] == "THREE", "MyEnum.THREE is not serialized to 'THREE'"
    assert TestMessage(x=TestMessageMyEnum.FOUR).to_dict()['x'] == "FOUR", "MyEnum.FOUR is not serialized to 'FOUR'"
