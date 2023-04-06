from dataclasses import dataclass
from typing import List

import bananaproto


@dataclass
class TestMessage(bananaproto.Message):
    foo: int = bananaproto.uint32_field(0)
    bar: str = bananaproto.string_field(1)
    baz: float = bananaproto.float_field(2)


@dataclass
class TestNestedChildMessage(bananaproto.Message):
    str_key: str = bananaproto.string_field(0)
    bytes_key: bytes = bananaproto.bytes_field(1)
    bool_key: bool = bananaproto.bool_field(2)
    float_key: float = bananaproto.float_field(3)
    int_key: int = bananaproto.uint64_field(4)


@dataclass
class TestNestedMessage(bananaproto.Message):
    foo: TestNestedChildMessage = bananaproto.message_field(0)
    bar: TestNestedChildMessage = bananaproto.message_field(1)
    baz: TestNestedChildMessage = bananaproto.message_field(2)


@dataclass
class TestRepeatedMessage(bananaproto.Message):
    foo_repeat: List[str] = bananaproto.string_field(0)
    bar_repeat: List[int] = bananaproto.int64_field(1)
    baz_repeat: List[bool] = bananaproto.bool_field(2)


class BenchMessage:
    """Test creation and usage a proto message."""

    def setup(self):
        self.cls = TestMessage
        self.instance = TestMessage()
        self.instance_filled = TestMessage(0, "test", 0.0)
        self.instance_filled_bytes = bytes(self.instance_filled)
        self.instance_filled_nested = TestNestedMessage(
            TestNestedChildMessage("foo", bytearray(b"test1"), True, 0.1234, 500),
            TestNestedChildMessage("bar", bytearray(b"test2"), True, 3.1415, -302),
            TestNestedChildMessage("baz", bytearray(b"test3"), False, 1e5, 300),
        )
        self.instance_filled_nested_bytes = bytes(self.instance_filled_nested)
        self.instance_filled_repeated = TestRepeatedMessage(
            [
                "test1",
                "test2",
                "test3",
                "test4",
                "test5",
                "test6",
                "test7",
                "test8",
                "test9",
                "test10",
            ],
            [2, -100, 0, 500000, 600, -425678, 1000000000, -300, 1, -694214214466],
            [True, False, False, False, True, True, False, True, False, False],
        )
        self.instance_filled_repeated_bytes = bytes(self.instance_filled_repeated)

    def time_overhead(self):
        """Overhead in class definition."""

        @dataclass
        class Message(bananaproto.Message):
            foo: int = bananaproto.uint32_field(0)
            bar: str = bananaproto.string_field(1)
            baz: float = bananaproto.float_field(2)

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
