from betterproto.tests.output_betterproto.to_dict_with_missing_enum.to_dict_with_missing_enum import TestMessage


def test_message_attributes():
    assert TestMessage(x=TestMessage.MyEnum.ONE).to_dict()['x'] == "ONE", "MyEnum.ONE is not serialized to 'ONE'"
    assert TestMessage(x=TestMessage.MyEnum.THREE).to_dict()['x'] == "THREE", "MyEnum.THREE is not serialized to 'THREE'"
    assert TestMessage(x=TestMessage.MyEnum.FOUR).to_dict()['x'] == "FOUR", "MyEnum.FOUR is not serialized to 'FOUR'"
