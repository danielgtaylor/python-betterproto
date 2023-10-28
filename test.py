from dataclasses import dataclass
from typing import List

import betterproto


def test_serializing():
    @dataclass(eq=False, repr=False)
    class Y(betterproto.Message):
        count: float = betterproto.double_field(1)

    @dataclass(eq=False, repr=False)
    class X(betterproto.Message):
        # For some reason this leading field is necessary to trigger this condition.
        name: str = betterproto.string_field(1)
        y: List[Y] = betterproto.message_field(2)

    x = X(name="fun", y=[Y(count=0), Y(count=1)])
    encoded_x = x.SerializeToString()
    decoded_x = X.FromString(encoded_x)

    assert decoded_x == X(name="fun", y=[Y(count=0), Y(count=1)])
