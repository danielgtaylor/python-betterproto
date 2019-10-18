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
