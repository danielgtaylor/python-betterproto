import betterproto
from dataclasses import dataclass


@dataclass
class TestMessage(betterproto.Message):
    foo: int = betterproto.uint32_field(0)
    bar: str = betterproto.string_field(1)
    baz: float = betterproto.float_field(2)

class BenchMessage:
    """
    An example benchmark that times the performance of various kinds
    of iterating over dictionaries in Python.
    """
    def setup(self):
        self.cls = TestMessage
        self.instance = TestMessage()

    def time_overhead(self):
        """Overhead in class definition.
        """
        for _ in range(100):
            @dataclass
            class Message(betterproto.Message):
                foo: int = betterproto.uint32_field(0)
                bar: str = betterproto.string_field(1)
                baz: float = betterproto.float_field(2)

    def time_instantiation(self):
        """Time instantiation
        """
        self.cls()

    def time_attribute_access(self):
        """Time to access an attribute
        """
        self.instance.foo
        self.instance.bar
        self.instance.baz
    
    def time_attribute_setting_init(self):
        """Time to set an attribute
        """
        self.cls(0, "test", 0.0)

    def time_attribute_setting(self):
        """Time to set an attribute
        """
        self.instance.foo = 0
        self.instance.bar = "test"
        self.instance.baz = 0.0


class MemSuite:
    def setup(self):
        self.cls = TestMessage
    
    def mem_instance(self):
        return self.cls()
