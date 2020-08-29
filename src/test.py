import pyximport

pyximport.install()
import tests

exit()
import timeit
from dataclasses import dataclass

import betterproto


class Message(betterproto.Message):
    foo: int = betterproto.uint32_field(0)
    bar: int = betterproto.uint32_field(1)
    baz: int = betterproto.uint32_field(2)


from pympler.asizeof import asizeof as size


timeit.main(
    [
        f"-sfrom message import Message; from dataclasses import dataclass; import betterproto",
        "-n 100000",
        "-v",
        """
@dataclass
class Message(betterproto.Message):
    foo: int = betterproto.uint32_field(0)
    bar: int = betterproto.uint32_field(1)
    baz: int = betterproto.uint32_field(2)
        """,
    ]
)
