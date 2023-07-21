import json
import sys
from copy import (
    copy,
    deepcopy,
)
from dataclasses import dataclass
from datetime import (
    datetime,
    timedelta,
)
from inspect import (
    Parameter,
    signature,
)
from typing import (
    Dict,
    List,
    Optional,
)

import pytest

import betterproto


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
    assert foo.to_pydict() == {"name": "foo", "child": {"name": "bar"}}


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

    # Similar expectations for pydict
    foo = Foo().from_pydict({"bar": 1})
    assert foo.bar == TestEnum.ONE
    assert foo.to_pydict() == {"bar": TestEnum.ONE}


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
    assert not hasattr(foo, "bar")
    assert object.__getattribute__(foo, "bar") == betterproto.PLACEHOLDER
    assert betterproto.which_one_of(foo, "group1")[0] == "baz"

    foo.sub = Sub(val=1)
    assert betterproto.serialized_on_wire(foo.sub)

    foo.abc = "test"

    # Group 1 shouldn't be touched, group 2 should have reset
    assert not hasattr(foo, "sub")
    assert object.__getattribute__(foo, "sub") == betterproto.PLACEHOLDER
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


@pytest.mark.skipif(
    sys.version_info < (3, 10),
    reason="pattern matching is only supported in python3.10+",
)
def test_oneof_pattern_matching():
    from .oneof_pattern_matching import test_oneof_pattern_matching

    test_oneof_pattern_matching()


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
    assert json.loads(test.to_json()) == {
        "pascalCase": 1,
        "camelCase": 2,
        "snakeCase": 3,
        "kabobCase": 4,
    }

    assert json.loads(test.to_json(casing=betterproto.Casing.SNAKE)) == {
        "pascal_case": 1,
        "camel_case": 2,
        "snake_case": 3,
        "kabob_case": 4,
    }


def test_dict_casing():
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
    assert test.to_pydict() == {
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
    assert test.to_pydict(casing=betterproto.Casing.SNAKE) == {
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


def test_optional_datetime_to_dict():
    @dataclass
    class Request(betterproto.Message):
        date: Optional[datetime] = betterproto.message_field(1, optional=True)

    # Check dict serialization
    assert Request().to_dict() == {}
    assert Request().to_dict(include_default_values=True) == {"date": None}
    assert Request(date=datetime(2020, 1, 1)).to_dict() == {
        "date": "2020-01-01T00:00:00Z"
    }
    assert Request(date=datetime(2020, 1, 1)).to_dict(include_default_values=True) == {
        "date": "2020-01-01T00:00:00Z"
    }

    # Check pydict serialization
    assert Request().to_pydict() == {}
    assert Request().to_pydict(include_default_values=True) == {"date": None}
    assert Request(date=datetime(2020, 1, 1)).to_pydict() == {
        "date": datetime(2020, 1, 1)
    }
    assert Request(date=datetime(2020, 1, 1)).to_pydict(
        include_default_values=True
    ) == {"date": datetime(2020, 1, 1)}


def test_to_json_default_values():
    @dataclass
    class TestMessage(betterproto.Message):
        some_int: int = betterproto.int32_field(1)
        some_double: float = betterproto.double_field(2)
        some_str: str = betterproto.string_field(3)
        some_bool: bool = betterproto.bool_field(4)

    # Empty dict
    test = TestMessage().from_dict({})

    assert json.loads(test.to_json(include_default_values=True)) == {
        "someInt": 0,
        "someDouble": 0.0,
        "someStr": "",
        "someBool": False,
    }

    # All default values
    test = TestMessage().from_dict(
        {"someInt": 0, "someDouble": 0.0, "someStr": "", "someBool": False}
    )

    assert json.loads(test.to_json(include_default_values=True)) == {
        "someInt": 0,
        "someDouble": 0.0,
        "someStr": "",
        "someBool": False,
    }


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

    test = TestMessage().from_pydict({})

    assert test.to_pydict(include_default_values=True) == {
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

    test = TestMessage().from_pydict(
        {"someInt": 0, "someDouble": 0.0, "someStr": "", "someBool": False}
    )

    assert test.to_pydict(include_default_values=True) == {
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

    test = TestMessage2().from_pydict(
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

    assert test.to_pydict(include_default_values=True) == {
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

    test = TestParentMessage().from_pydict({"someInt": 0, "someDouble": 1.2})

    assert test.to_pydict(include_default_values=True) == {
        "someInt": 0,
        "someDouble": 1.2,
        "someMessage": {"someOtherInt": 0},
    }


def test_to_dict_datetime_values():
    @dataclass
    class TestDatetimeMessage(betterproto.Message):
        bar: datetime = betterproto.message_field(1)
        baz: timedelta = betterproto.message_field(2)

    test = TestDatetimeMessage().from_dict(
        {"bar": "2020-01-01T00:00:00Z", "baz": "86400.000s"}
    )

    assert test.to_dict() == {"bar": "2020-01-01T00:00:00Z", "baz": "86400.000s"}

    test = TestDatetimeMessage().from_pydict(
        {"bar": datetime(year=2020, month=1, day=1), "baz": timedelta(days=1)}
    )

    assert test.to_pydict() == {
        "bar": datetime(year=2020, month=1, day=1),
        "baz": timedelta(days=1),
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
        Intermediate,
        Test as RecursiveMessage,
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


# valid ISO datetimes according to https://www.myintervals.com/blog/2009/05/20/iso-8601-date-validation-that-doesnt-suck/
iso_candidates = """2009-12-12T12:34
2009
2009-05-19
2009-05-19
20090519
2009123
2009-05
2009-123
2009-222
2009-001
2009-W01-1
2009-W51-1
2009-W33
2009W511
2009-05-19
2009-05-19 00:00
2009-05-19 14
2009-05-19 14:31
2009-05-19 14:39:22
2009-05-19T14:39Z
2009-W21-2
2009-W21-2T01:22
2009-139
2009-05-19 14:39:22-06:00
2009-05-19 14:39:22+0600
2009-05-19 14:39:22-01
20090621T0545Z
2007-04-06T00:00
2007-04-05T24:00
2010-02-18T16:23:48.5
2010-02-18T16:23:48,444
2010-02-18T16:23:48,3-06:00
2010-02-18T16:23:00.4
2010-02-18T16:23:00,25
2010-02-18T16:23:00.33+0600
2010-02-18T16:00:00.23334444
2010-02-18T16:00:00,2283
2009-05-19 143922
2009-05-19 1439""".split(
    "\n"
)


def test_iso_datetime():
    @dataclass
    class Envelope(betterproto.Message):
        ts: datetime = betterproto.message_field(1)

    msg = Envelope()

    for _, candidate in enumerate(iso_candidates):
        msg.from_dict({"ts": candidate})
        assert isinstance(msg.ts, datetime)


def test_iso_datetime_list():
    @dataclass
    class Envelope(betterproto.Message):
        timestamps: List[datetime] = betterproto.message_field(1)

    msg = Envelope()

    msg.from_dict({"timestamps": iso_candidates})
    assert all([isinstance(item, datetime) for item in msg.timestamps])


def test_service_argument__expected_parameter():
    from tests.output_betterproto.service import TestStub

    sig = signature(TestStub.do_thing)
    do_thing_request_parameter = sig.parameters["do_thing_request"]
    assert do_thing_request_parameter.default is Parameter.empty
    assert do_thing_request_parameter.annotation == "DoThingRequest"


def test_copyability():
    @dataclass
    class Spam(betterproto.Message):
        foo: bool = betterproto.bool_field(1)
        bar: int = betterproto.int32_field(2)
        baz: List[str] = betterproto.string_field(3)

    spam = Spam(bar=12, baz=["hello"])
    copied = copy(spam)
    assert spam == copied
    assert spam is not copied
    assert spam.baz is copied.baz

    deepcopied = deepcopy(spam)
    assert spam == deepcopied
    assert spam is not deepcopied
    assert spam.baz is not deepcopied.baz


def test_is_set():
    @dataclass
    class Spam(betterproto.Message):
        foo: bool = betterproto.bool_field(1)
        bar: Optional[int] = betterproto.int32_field(2, optional=True)

    assert not Spam().is_set("foo")
    assert not Spam().is_set("bar")
    assert Spam(foo=True).is_set("foo")
    assert Spam(foo=True, bar=0).is_set("bar")
