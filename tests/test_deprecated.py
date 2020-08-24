import pytest

from tests.output_betterproto.deprecated import Test as DeprecatedMessageTest
from tests.output_betterproto.deprecated_field import Test as DeprecatedFieldTest


def test_deprecated_message():
    with pytest.deprecated_call():
        DeprecatedMessageTest(value=10)


def test_deprecated_message_with_deprecated_field():
    with pytest.warns(None) as record:
        DeprecatedMessageTest(v=10, value=10)
    assert len(record) == 2


def test_deprecated_field_warning():
    with pytest.deprecated_call():
        DeprecatedFieldTest(v=10, value=10)


def test_deprecated_field_no_warning():
    with pytest.warns(None) as record:
        DeprecatedFieldTest(value=10)
    assert not record
