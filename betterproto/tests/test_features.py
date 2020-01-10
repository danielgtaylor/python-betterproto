import betterproto
from dataclasses import dataclass
from typing import Optional


def test_has_field():
    @dataclass
    class Bar(betterproto.Message):
        baz: int = betterproto.int32_field(1)

    @dataclass
    class Foo(betterproto.Message):
        bar: Bar = betterproto.message_field(1)

    # Unset by default
    foo = Foo()
    assert betterproto.serialized_on_wire(foo.bar) == False

    # Serialized after setting something
    foo.bar.baz = 1
    assert betterproto.serialized_on_wire(foo.bar) == True

    # Still has it after setting the default value
    foo.bar.baz = 0
    assert betterproto.serialized_on_wire(foo.bar) == True

    # Manual override (don't do this)
    foo.bar._serialized_on_wire = False
    assert betterproto.serialized_on_wire(foo.bar) == False

    # Can manually set it but defaults to false
    foo.bar = Bar()
    assert betterproto.serialized_on_wire(foo.bar) == False


def test_class_init():
    @dataclass
    class Bar(betterproto.Message):
        name: str = betterproto.string_field(1)

    @dataclass
    class Foo(betterproto.Message):
        name: str = betterproto.string_field(1)
        child: Bar = betterproto.message_field(2)

    foo = Foo(name="foo", child=Bar(name="bar"))

    assert foo.to_dict() == {"name": "foo", "child": {"name": "bar"}}


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


def test_oneof_support():
    @dataclass
    class Sub(betterproto.Message):
        val: int = betterproto.int32_field(1)

    @dataclass
    class Foo(betterproto.Message):
        bar: int = betterproto.int32_field(1, group="group1")
        baz: str = betterproto.string_field(2, group="group1")
        sub: Sub = betterproto.message_field(3, group="group2")
        abc: str = betterproto.string_field(4, group="group2")

    foo = Foo()

    assert betterproto.which_one_of(foo, "group1")[0] == ""

    foo.bar = 1
    foo.baz = "test"

    # Other oneof fields should now be unset
    assert foo.bar == 0
    assert betterproto.which_one_of(foo, "group1")[0] == "baz"

    foo.sub.val = 1
    assert betterproto.serialized_on_wire(foo.sub)

    foo.abc = "test"

    # Group 1 shouldn't be touched, group 2 should have reset
    assert foo.sub.val == 0
    assert betterproto.serialized_on_wire(foo.sub) == False
    assert betterproto.which_one_of(foo, "group2")[0] == "abc"

    # Zero value should always serialize for one-of
    foo = Foo(bar=0)
    assert betterproto.which_one_of(foo, "group1")[0] == "bar"
    assert bytes(foo) == b"\x08\x00"

    # Round trip should also work
    foo2 = Foo().parse(bytes(foo))
    assert betterproto.which_one_of(foo2, "group1")[0] == "bar"
    assert foo.bar == 0
    assert betterproto.which_one_of(foo2, "group2")[0] == ""


def test_json_casing():
    @dataclass
    class CasingTest(betterproto.Message):
        pascal_case: int = betterproto.int32_field(1)
        camel_case: int = betterproto.int32_field(2)
        snake_case: int = betterproto.int32_field(3)
        kabob_case: int = betterproto.int32_field(4)

    # Parsing should accept almost any input
    test = CasingTest().from_dict(
        {"PascalCase": 1, "camelCase": 2, "snake_case": 3, "kabob-case": 4}
    )

    assert test == CasingTest(1, 2, 3, 4)

    # Serializing should be strict.
    assert test.to_dict() == {
        "pascalCase": 1,
        "camelCase": 2,
        "snakeCase": 3,
        "kabobCase": 4,
    }

    assert test.to_dict(casing=betterproto.Casing.SNAKE) == {
        "pascal_case": 1,
        "camel_case": 2,
        "snake_case": 3,
        "kabob_case": 4,
    }


def test_optional_flag():
    @dataclass
    class Request(betterproto.Message):
        flag: Optional[bool] = betterproto.message_field(1, wraps=betterproto.TYPE_BOOL)

    # Serialization of not passed vs. set vs. zero-value.
    assert bytes(Request()) == b""
    assert bytes(Request(flag=True)) == b"\n\x02\x08\x01"
    assert bytes(Request(flag=False)) == b"\n\x00"

    # Differentiate between not passed and the zero-value.
    assert Request().parse(b"").flag == None
    assert Request().parse(b"\n\x00").flag == False
