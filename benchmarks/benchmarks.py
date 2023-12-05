from dataclasses import dataclass
from typing import List

import betterproto


@dataclass
class TestMessage(betterproto.Message):
    foo: int = betterproto.uint32_field(1)
    bar: str = betterproto.string_field(2)
    baz: float = betterproto.float_field(3)


@dataclass
class TestNestedChildMessage(betterproto.Message):
    str_key: str = betterproto.string_field(1)
    bytes_key: bytes = betterproto.bytes_field(2)
    bool_key: bool = betterproto.bool_field(3)
    float_key: float = betterproto.float_field(4)
    int_key: int = betterproto.uint64_field(5)


@dataclass
class TestNestedMessage(betterproto.Message):
    foo: TestNestedChildMessage = betterproto.message_field(1)
    bar: TestNestedChildMessage = betterproto.message_field(2)
    baz: TestNestedChildMessage = betterproto.message_field(3)


@dataclass
class TestRepeatedMessage(betterproto.Message):
    foo_repeat: List[str] = betterproto.string_field(1)
    bar_repeat: List[int] = betterproto.int64_field(2)
    baz_repeat: List[bool] = betterproto.bool_field(3)


class BenchMessage:
    """Test creation and usage a proto message."""

    def setup(self):
        self.cls = TestMessage
        self.instance = TestMessage()
        self.instance_filled = TestMessage(0, "test", 0.0)
        self.instance_filled_bytes = bytes(self.instance_filled)
        self.instance_filled_nested = TestNestedMessage(
            TestNestedChildMessage("foo", bytearray(b"test1"), True, 0.1234, 500),
            TestNestedChildMessage("bar", bytearray(b"test2"), True, 3.1415, 302),
            TestNestedChildMessage("baz", bytearray(b"test3"), False, 1e5, 300),
        )
        self.instance_filled_nested_bytes = bytes(self.instance_filled_nested)
        self.instance_filled_repeated = TestRepeatedMessage(
            [f"test{i}" for i in range(1_000)],
            [(i - 500) ** 3 for i in range(1_000)],
            [i % 2 == 0 for i in range(1_000)],
        )
        self.instance_filled_repeated_bytes = bytes(self.instance_filled_repeated)

    def time_overhead(self):
        """Overhead in class definition."""

        @dataclass
        class Message(betterproto.Message):
            foo: int = betterproto.uint32_field(1)
            bar: str = betterproto.string_field(2)
            baz: float = betterproto.float_field(3)

    def time_instantiation(self):
        """Time instantiation"""
        self.cls()

    def time_attribute_access(self):
        """Time to access an attribute"""
        self.instance.foo
        self.instance.bar
        self.instance.baz

    def time_init_with_values(self):
        """Time to set an attribute"""
        self.cls(0, "test", 0.0)

    def time_attribute_setting(self):
        """Time to set attributes"""
        self.instance.foo = 0
        self.instance.bar = "test"
        self.instance.baz = 0.0

    def time_serialize(self):
        """Time serializing a message to wire."""
        bytes(self.instance_filled)

    def time_deserialize(self):
        """Time deserialize a message."""
        TestMessage().parse(self.instance_filled_bytes)

    def time_serialize_nested(self):
        """Time serializing a nested message to wire."""
        bytes(self.instance_filled_nested)

    def time_deserialize_nested(self):
        """Time deserialize a nested message."""
        TestNestedMessage().parse(self.instance_filled_nested_bytes)

    def time_serialize_repeated(self):
        """Time serializing a repeated message to wire."""
        bytes(self.instance_filled_repeated)

    def time_deserialize_repeated(self):
        """Time deserialize a repeated message."""
        TestRepeatedMessage().parse(self.instance_filled_repeated_bytes)


class MemSuite:
    def setup(self):
        self.cls = TestMessage

    def mem_instance(self):
        return self.cls()
