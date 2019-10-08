import struct
from typing import Union, Generator, Any, SupportsBytes, List, Tuple
from dataclasses import dataclass


def parse_varint(buffer: bytes, pos: int, signed: bool = False) -> Tuple[int, int]:
    """Parse a single varint value from a byte buffer."""
    result = 0
    shift = 0
    while 1:
        b = buffer[pos]
        result |= (b & 0x7F) << shift
        pos += 1
        if not (b & 0x80):
            return (result, pos)
        shift += 7
        if shift >= 64:
            raise ValueError("Too many bytes when decoding varint.")


@dataclass(frozen=True)
class ParsedField:
    number: int
    wire_type: int
    value: Any


def fields(value: bytes) -> Generator[ParsedField, None, None]:
    i = 0
    while i < len(value):
        num_wire, i = parse_varint(value, i)
        # print(num_wire, i)
        number = num_wire >> 3
        wire_type = num_wire & 0x7

        if wire_type == 0:
            decoded, i = parse_varint(value, i)
        elif wire_type == 1:
            decoded, i = value[i : i + 8], i + 8
        elif wire_type == 2:
            length, i = parse_varint(value, i)
            decoded = value[i : i + length]
            i += length
        elif wire_type == 5:
            decoded, i = value[i : i + 4], i + 4
        else:
            raise NotImplementedError(f"Wire type {wire_type}")

        # print(ParsedField(number=number, wire_type=wire_type, value=decoded))

        yield ParsedField(number=number, wire_type=wire_type, value=decoded)
