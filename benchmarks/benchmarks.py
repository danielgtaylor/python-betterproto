import betterproto


class TestMessage(betterproto.Message):
    foo: int = betterproto.uint32_field(0)
    bar: str = betterproto.string_field(1)
    baz: float = betterproto.float_field(2)


class BenchMessage:
    """Test creation and usage a proto message."""

    def setup(self):
        self.cls = TestMessage
        self.instance = TestMessage()
        self.instance_filled = TestMessage(0, "test", 0.0)

    def time_overhead(self):
        """Overhead in class definition."""

        class Message(betterproto.Message):
            foo: int = betterproto.uint32_field(0)
            bar: str = betterproto.string_field(1)
            baz: float = betterproto.float_field(2)

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


class MemSuite:
    def setup(self):
        self.cls = TestMessage

    def mem_instance(self):
        return self.cls()
