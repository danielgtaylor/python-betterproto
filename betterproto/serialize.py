import struct
from typing import Union, Generator, Any, SupportsBytes, List, Tuple
from dataclasses import dataclass


def _varint(value: int) -> bytes:
    # From https://github.com/protocolbuffers/protobuf/blob/master/python/google/protobuf/internal/encoder.py#L372
    b: List[int] = []

    if value < 0:
        value += 1 << 64

    bits = value & 0x7F
    value >>= 7
    while value:
        b.append(0x80 | bits)
        bits = value & 0x7F
        value >>= 7
        print(value)
    return bytes(b + [bits])
