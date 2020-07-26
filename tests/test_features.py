import betterproto
from dataclasses import dataclass
from typing import Optional, List, Dict


def test_has_field():
    @dataclass
    class Bar(betterproto.Message):
        baz: int = betterproto.int32_field(1)

    @dataclass
    class Foo(betterproto.Message):
        bar: Bar = betterproto.message_field(1)

    # Unset by default
    foo = Foo()
    assert betterproto.serialized_on_wire(foo.bar) is False

    # Serialized after setting something
    foo.bar.baz = 1
    assert betterproto.serialized_on_wire(foo.bar) is True

    # Still has it after setting the default value
    foo.bar.baz = 0
    assert betterproto.serialized_on_wire(foo.bar) is True

    # Manual override (don't do this)
    foo.bar._serialized_on_wire = False
    assert betterproto.serialized_on_wire(foo.bar) is False

    # Can manually set it but defaults to false
    foo.bar = Bar()
    assert betterproto.serialized_on_wire(foo.bar) is False

    @dataclass
    class WithCollections(betterproto.Message):
        test_list: List[str] = betterproto.string_field(1)
        test_map: Dict[str, str] = betterproto.map_field(
            2, betterproto.TYPE_STRING, betterproto.TYPE_STRING
        )

    # Is always set from parse, even if all collections are empty
    with_collections_empty = WithCollections().parse(bytes(WithCollections()))
    assert betterproto.serialized_on_wire(with_collections_empty) == True
    with_collections_list = WithCollections().parse(
        bytes(WithCollections(test_list=["a", "b", "c"]))
    )
    assert betterproto.serialized_on_wire(with_collections_list) == True
    with_collections_map = WithCollections().parse(
        bytes(WithCollections(test_map={"a": "b", "c": "d"}))
    )
    assert betterproto.serialized_on_wire(with_collections_map) == True


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
    assert betterproto.serialized_on_wire(foo.sub) is False
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
    assert Request().parse(b"").flag is None
    assert Request().parse(b"\n\x00").flag is False


def test_to_dict_default_values():
    @dataclass
    class TestMessage(betterproto.Message):
        some_int: int = betterproto.int32_field(1)
        some_double: float = betterproto.double_field(2)
        some_str: str = betterproto.string_field(3)
        some_bool: bool = betterproto.bool_field(4)

    # Empty dict
    test = TestMessage().from_dict({})

    assert test.to_dict(include_default_values=True) == {
        "someInt": 0,
        "someDouble": 0.0,
        "someStr": "",
        "someBool": False,
    }

    # All default values
    test = TestMessage().from_dict(
        {"someInt": 0, "someDouble": 0.0, "someStr": "", "someBool": False}
    )

    assert test.to_dict(include_default_values=True) == {
        "someInt": 0,
        "someDouble": 0.0,
        "someStr": "",
        "someBool": False,
    }

    # Some default and some other values
    @dataclass
    class TestMessage2(betterproto.Message):
        some_int: int = betterproto.int32_field(1)
        some_double: float = betterproto.double_field(2)
        some_str: str = betterproto.string_field(3)
        some_bool: bool = betterproto.bool_field(4)
        some_default_int: int = betterproto.int32_field(5)
        some_default_double: float = betterproto.double_field(6)
        some_default_str: str = betterproto.string_field(7)
        some_default_bool: bool = betterproto.bool_field(8)

    test = TestMessage2().from_dict(
        {
            "someInt": 2,
            "someDouble": 1.2,
            "someStr": "hello",
            "someBool": True,
            "someDefaultInt": 0,
            "someDefaultDouble": 0.0,
            "someDefaultStr": "",
            "someDefaultBool": False,
        }
    )

    assert test.to_dict(include_default_values=True) == {
        "someInt": 2,
        "someDouble": 1.2,
        "someStr": "hello",
        "someBool": True,
        "someDefaultInt": 0,
        "someDefaultDouble": 0.0,
        "someDefaultStr": "",
        "someDefaultBool": False,
    }

    # Nested messages
    @dataclass
    class TestChildMessage(betterproto.Message):
        some_other_int: int = betterproto.int32_field(1)

    @dataclass
    class TestParentMessage(betterproto.Message):
        some_int: int = betterproto.int32_field(1)
        some_double: float = betterproto.double_field(2)
        some_message: TestChildMessage = betterproto.message_field(3)

    test = TestParentMessage().from_dict({"someInt": 0, "someDouble": 1.2})

    assert test.to_dict(include_default_values=True) == {
        "someInt": 0,
        "someDouble": 1.2,
        "someMessage": {"someOtherInt": 0},
    }


def test_oneof_default_value_set_causes_writes_wire():
    @dataclass
    class Empty(betterproto.Message):
        pass

    @dataclass
    class Foo(betterproto.Message):
        bar: int = betterproto.int32_field(1, group="group1")
        baz: str = betterproto.string_field(2, group="group1")
        qux: Empty = betterproto.message_field(3, group="group1")

    def _round_trip_serialization(foo: Foo) -> Foo:
        return Foo().parse(bytes(foo))

    foo1 = Foo(bar=0)
    foo2 = Foo(baz="")
    foo3 = Foo(qux=Empty())
    foo4 = Foo()

    assert bytes(foo1) == b"\x08\x00"
    assert (
        betterproto.which_one_of(foo1, "group1")
        == betterproto.which_one_of(_round_trip_serialization(foo1), "group1")
        == ("bar", 0)
    )

    assert bytes(foo2) == b"\x12\x00"  # Baz is just an empty string
    assert (
        betterproto.which_one_of(foo2, "group1")
        == betterproto.which_one_of(_round_trip_serialization(foo2), "group1")
        == ("baz", "")
    )

    assert bytes(foo3) == b"\x1a\x00"
    assert (
        betterproto.which_one_of(foo3, "group1")
        == betterproto.which_one_of(_round_trip_serialization(foo3), "group1")
        == ("qux", Empty())
    )

    assert bytes(foo4) == b""
    assert (
        betterproto.which_one_of(foo4, "group1")
        == betterproto.which_one_of(_round_trip_serialization(foo4), "group1")
        == ("", None)
    )


def test_recursive_message():
    from tests.output_betterproto.recursivemessage import Test as RecursiveMessage

    msg = RecursiveMessage()

    assert msg.child == RecursiveMessage()

    # Lazily-created zero-value children must not affect equality.
    assert msg == RecursiveMessage()

    # Lazily-created zero-value children must not affect serialization.
    assert bytes(msg) == b""


def test_recursive_message_defaults():
    from tests.output_betterproto.recursivemessage import (
        Test as RecursiveMessage,
        Intermediate,
    )

    msg = RecursiveMessage(name="bob", intermediate=Intermediate(42))

    # set values are as expected
    assert msg == RecursiveMessage(name="bob", intermediate=Intermediate(42))

    # lazy initialized works modifies the message
    assert msg != RecursiveMessage(
        name="bob", intermediate=Intermediate(42), child=RecursiveMessage(name="jude")
    )
    msg.child.child.name = "jude"
    assert msg == RecursiveMessage(
        name="bob",
        intermediate=Intermediate(42),
        child=RecursiveMessage(child=RecursiveMessage(name="jude")),
    )

    # lazily initialization recurses as needed
    assert msg.child.child.child.child.child.child.child == RecursiveMessage()
    assert msg.intermediate.child.intermediate == Intermediate()


def test_message_repr():
    from tests.output_betterproto.recursivemessage import Test

    assert repr(Test(name="Loki")) == "Test(name='Loki')"
    assert repr(Test(child=Test(), name="Loki")) == "Test(name='Loki', child=Test())"


def test_bool():
    """Messages should evaluate similarly to a collection
    >>> test = []
    >>> bool(test)
    ... False
    >>> test.append(1)
    >>> bool(test)
    ... True
    >>> del test[0]
    >>> bool(test)
    ... False
    """

    @dataclass
    class Falsy(betterproto.Message):
        pass

    @dataclass
    class Truthy(betterproto.Message):
        bar: int = betterproto.int32_field(1)

    assert not Falsy()
    t = Truthy()
    assert not t
    t.bar = 1
    assert t
    t.bar = 0
    assert not t
