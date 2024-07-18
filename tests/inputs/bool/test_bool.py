import pytest

from tests.output_betterproto.bool import Test
from tests.output_betterproto_pydantic.bool import Test as TestPyd


def test_value():
    message = Test()
    assert not message.value, "Boolean is False by default"


def test_pydantic_no_value():
    message = TestPyd()
    assert not message.value, "Boolean is False by default"


def test_pydantic_value():
    message = TestPyd(value=False)
    assert not message.value


def test_pydantic_bad_value():
    with pytest.raises(ValueError):
        TestPyd(value=123)

