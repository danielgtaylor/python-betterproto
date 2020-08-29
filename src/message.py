from dataclasses import dataclass

import betterproto


class Message(betterproto.Message):
    foo: int = betterproto.uint32_field(0)
    bar: int = betterproto.uint32_field(1)
    baz: int = betterproto.uint32_field(2)


print(Message()._serialized_on_wire)
