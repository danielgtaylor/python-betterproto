import betterproto
from dataclasses import dataclass


def test_has_field():
    @dataclass
    class Bar(betterproto.Message):
        baz: int = betterproto.int32_field(1)

    @dataclass
    class Foo(betterproto.Message):
        bar: Bar = betterproto.message_field(1)

    # Unset by default
    foo = Foo()
    assert foo.bar.serialized_on_wire == False

    # Serialized after setting something
    foo.bar.baz = 1
    assert foo.bar.serialized_on_wire == True

    # Still has it after setting the default value
    foo.bar.baz = 0
    assert foo.bar.serialized_on_wire == True

    # Manual override
    foo.bar.serialized_on_wire = False
    assert foo.bar.serialized_on_wire == False

    # Can manually set it but defaults to false
    foo.bar = Bar()
    assert foo.bar.serialized_on_wire == False


def test_enum_as_int_json():
    class TestEnum(betterproto.Enum):
        ZERO = 0
        ONE = 1

    @dataclass
    class Foo(betterproto.Message):
        bar: TestEnum = betterproto.enum_field(1)

    # JSON strings are supported, but ints should still be supported too.
    foo = Foo().from_dict({"bar": 1})
    assert foo.bar == TestEnum.ONE

    # Plain-ol'-ints should serialize properly too.
    foo.bar = 1
    assert foo.to_dict() == {"bar": "ONE"}


def test_unknown_fields():
    @dataclass
    class Newer(betterproto.Message):
        foo: bool = betterproto.bool_field(1)
        bar: int = betterproto.int32_field(2)
        baz: str = betterproto.string_field(3)

    @dataclass
    class Older(betterproto.Message):
        foo: bool = betterproto.bool_field(1)

    newer = Newer(foo=True, bar=1, baz="Hello")
    serialized_newer = bytes(newer)

    # Unknown fields in `Newer` should round trip with `Older`
    round_trip = bytes(Older().parse(serialized_newer))
    assert serialized_newer == round_trip

    new_again = Newer().parse(round_trip)
    assert newer == new_again
