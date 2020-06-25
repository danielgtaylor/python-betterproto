from betterproto.tests.output_betterproto.enum_skipped_value.enum_skipped_value import (
    Test,
    TestMyEnum,
)
import pytest


@pytest.mark.xfail(reason="#93")
def test_message_attributes():
    assert (
        Test(x=TestMyEnum.ONE).to_dict()["x"] == "ONE"
    ), "MyEnum.ONE is not serialized to 'ONE'"
    assert (
        Test(x=TestMyEnum.THREE).to_dict()["x"] == "THREE"
    ), "MyEnum.THREE is not serialized to 'THREE'"
    assert (
        Test(x=TestMyEnum.FOUR).to_dict()["x"] == "FOUR"
    ), "MyEnum.FOUR is not serialized to 'FOUR'"
