import betterproto
from tests.output_betterproto.proto3_field_presence_oneof import (
    InnerNested,
    Nested,
    Test,
    WithOptional,
)


def test_serialization():
    """Ensure that serialization of fields unset but with explicit field
    presence do not bloat the serialized payload with length-delimited fields
    with length 0"""

    def test_empty_nested(message: Test) -> None:
        # '0a' => tag 1, length delimited
        # '00' => length: 0
        assert bytes(message) == bytearray.fromhex("0a 00")

    test_empty_nested(Test(nested=Nested()))
    test_empty_nested(Test(nested=Nested(inner=InnerNested(a=betterproto.NOT_SET))))

    def test_empty_with_optional(message: Test) -> None:
        # '12' => tag 2, length delimited
        # '00' => length: 0
        assert bytes(message) == bytearray.fromhex("12 00")

    test_empty_with_optional(Test(with_optional=WithOptional()))
    test_empty_with_optional(Test(with_optional=WithOptional(b=betterproto.NOT_SET)))
