from betterproto.tests.output_betterproto.to_dict_with_missing_enum.to_dict_with_missing_enum import (
    Test,
    TestMyEnum,
)
import pytest


@pytest.mark.xfail("#93")
def test_message_attributes():
    assert (
        Test(x=TestMyEnum.ONE).to_dict()['x'] == "ONE"
    ), "MyEnum.ONE is not serialized to 'ONE'"
    assert (
        Test(x=TestMyEnum.THREE).to_dict()['x'] == "THREE"
    ), "MyEnum.THREE is not serialized to 'THREE'"
    assert (
        Test(x=TestMyEnum.FOUR).to_dict()['x'] == "FOUR"
    ), "MyEnum.FOUR is not serialized to 'FOUR'"
