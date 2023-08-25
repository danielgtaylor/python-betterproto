# dev tests
# to be deleted later

import betterproto
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass(repr=False)
class Baz(betterproto.Message):
    a: float = betterproto.float_field(1, group = "x")
    b: int = betterproto.int64_field(2, group = "x")
    c: float = betterproto.float_field(3, group = "y")
    d: int = betterproto.int64_field(4, group = "y")
    e: Optional[int] = betterproto.int32_field(5, group = "_e", optional = True)

@dataclass(repr=False)
class Foo(betterproto.Message):
    x: int = betterproto.int32_field(1)
    y: float = betterproto.double_field(2)
    z: List[Baz] = betterproto.message_field(3)

class Enm(betterproto.Enum):
    A = 0
    B = 1
    C = 2

@dataclass(repr=False)
class Bar(betterproto.Message):
    foo1: Foo = betterproto.message_field(1)
    foo2: Foo = betterproto.message_field(2)
    packed: List[int] = betterproto.int64_field(3)
    enm: Enm = betterproto.enum_field(4)
    map: Dict[int, bool] = betterproto.map_field(5, betterproto.TYPE_INT64, betterproto.TYPE_BOOL)
    maybe: Optional[bool] = betterproto.message_field(6, wraps=betterproto.TYPE_BOOL)
    bts: bytes = betterproto.bytes_field(7)

# Native serialization happening here
buffer = bytes(
    Bar(
        foo1=Foo(1, 2.34),
        foo2=Foo(3, 4.56, [Baz(a = 1.234), Baz(b = 5, e=1), Baz(b = 2, d = 3)]),
        packed=[5, 3, 1],
        enm=Enm.B,
        map={
            1: True,
            42: False
        },
        maybe=True,
        bts=b'Hi There!'
    )
)

# Native deserialization happening here
bar = Bar().parse(buffer)
print(bar)
