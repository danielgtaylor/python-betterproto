import pickle
from copy import (
    copy,
    deepcopy,
)
from dataclasses import dataclass
from typing import (
    Dict,
    List,
)
from unittest.mock import ANY

import betterproto
from betterproto.lib.google import protobuf as google


def unpickled(message):
    return pickle.loads(pickle.dumps(message))


@dataclass(eq=False, repr=False)
class Fe(betterproto.Message):
    abc: str = betterproto.string_field(1)


@dataclass(eq=False, repr=False)
class Fi(betterproto.Message):
    abc: str = betterproto.string_field(1)


@dataclass(eq=False, repr=False)
class Fo(betterproto.Message):
    abc: str = betterproto.string_field(1)


@dataclass(eq=False, repr=False)
class NestedData(betterproto.Message):
    struct_foo: Dict[str, "google.Struct"] = betterproto.map_field(
        1, betterproto.TYPE_STRING, betterproto.TYPE_MESSAGE
    )
    map_str_any_bar: Dict[str, "google.Any"] = betterproto.map_field(
        2, betterproto.TYPE_STRING, betterproto.TYPE_MESSAGE
    )


@dataclass(eq=False, repr=False)
class Complex(betterproto.Message):
    foo_str: str = betterproto.string_field(1)
    fe: "Fe" = betterproto.message_field(3, group="grp")
    fi: "Fi" = betterproto.message_field(4, group="grp")
    fo: "Fo" = betterproto.message_field(5, group="grp")
    nested_data: "NestedData" = betterproto.message_field(6)
    mapping: Dict[str, "google.Any"] = betterproto.map_field(
        7, betterproto.TYPE_STRING, betterproto.TYPE_MESSAGE
    )


def test_pickling_complex_message():
    msg = Complex(
        foo_str="yep",
        fe=Fe(abc="1"),
        nested_data=NestedData(
            struct_foo={
                "foo": google.Struct(
                    fields={
                        "hello": google.Value(
                            list_value=google.ListValue(
                                values=[google.Value(string_value="world")]
                            )
                        )
                    }
                ),
            },
            map_str_any_bar={
                "key": google.Any(value=b"value"),
            },
        ),
        mapping={
            "message": google.Any(value=bytes(Fi(abc="hi"))),
            "string": google.Any(value=b"howdy"),
        },
    )
    deser = unpickled(msg)
    assert msg == deser
    assert msg.fe.abc == "1"
    assert msg.is_set("fi") is not True
    assert msg.mapping["message"] == google.Any(value=bytes(Fi(abc="hi")))
    assert msg.mapping["string"].value.decode() == "howdy"
    assert (
        msg.nested_data.struct_foo["foo"]
        .fields["hello"]
        .list_value.values[0]
        .string_value
        == "world"
    )


def test_recursive_message():
    from tests.output_betterproto.recursivemessage import Test as RecursiveMessage

    msg = RecursiveMessage()
    msg = unpickled(msg)

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
    msg = unpickled(msg)

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


@dataclass
class Spam(betterproto.Message):
    foo: bool = betterproto.bool_field(1)
    bar: int = betterproto.int32_field(2)
    baz: List[str] = betterproto.string_field(3)


def test_copyability():
    msg = Spam(bar=12, baz=["hello"])
    msg = unpickled(msg)

    copied = copy(msg)
    assert msg == copied
    assert msg is not copied
    assert msg.baz is copied.baz

    deepcopied = deepcopy(msg)
    assert msg == deepcopied
    assert msg is not deepcopied
    assert msg.baz is not deepcopied.baz


def test_equality_comparison():
    from tests.output_betterproto.bool import Test as TestMessage

    msg = TestMessage(value=True)
    msg = unpickled(msg)
    assert msg == msg
    assert msg == ANY
    assert msg == TestMessage(value=True)
    assert msg != 1
    assert msg != TestMessage(value=False)
