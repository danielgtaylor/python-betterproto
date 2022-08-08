import pytest
from tests.output_betterproto.bool import Test
from tests.output_betterproto_pydantic.bool import Test as TestPyd


def test_value():
    message = Test()
    assert not message.value, "Boolean is False by default"


def test_pydantic_no_value():
    with pytest.raises(ValueError):
        TestPyd()


def test_pydantic_value():
    message = Test(value=False)
    assert not message.value
