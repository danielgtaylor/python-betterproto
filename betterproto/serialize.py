import struct
from typing import Union, Generator, Any, SupportsBytes, List, Tuple
from dataclasses import dataclass


def _varint(value: int) -> bytes:
    # From https://github.com/protocolbuffers/protobuf/blob/master/python/google/protobuf/internal/encoder.py#L372
    b: List[int] = []

    bits = value & 0x7F
    value >>= 7
    while value:
        b.append(0x80 | bits)
        bits = value & 0x7F
        value >>= 7
        print(value)
    return bytes(b + [bits])


def varint(field_number: int, value: Union[int, float]) -> bytes:
    key = _varint(field_number << 3)
    return key + _varint(value)


def len_delim(field_number: int, value: Union[str, bytes]) -> bytes:
    key = _varint((field_number << 3) | 2)

    if isinstance(value, str):
        value = value.encode("utf-8")

    return key + _varint(len(value)) + value


def packed(field_number: int, value: list) -> bytes:
    key = _varint((field_number << 3) | 2)

    packed = b""
    for item in value:
        if item < 0:
            # Handle negative numbers.
            item += 1 << 64
        packed += _varint(item)

    return key + _varint(len(packed)) + packed
