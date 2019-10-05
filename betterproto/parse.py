import struct
from typing import Union, Generator, Any, SupportsBytes, List, Tuple
from dataclasses import dataclass


def _decode_varint(
    buffer: bytes, pos: int, signed: bool = False, result_type: type = int
) -> Tuple[int, int]:
    result = 0
    shift = 0
    while 1:
        b = buffer[pos]
        result |= (b & 0x7F) << shift
        pos += 1
        if not (b & 0x80):
            result = result_type(result)
            return (result, pos)
        shift += 7
        if shift >= 64:
            raise ValueError("Too many bytes when decoding varint.")


def packed(value: bytes, signed: bool = False, result_type: type = int) -> list:
    parsed = []
    pos = 0
    while pos < len(value):
        decoded, pos = _decode_varint(
            value, pos, signed=signed, result_type=result_type
        )
        parsed.append(decoded)
    return parsed


@dataclass(frozen=True)
class Field:
    number: int
    wire_type: int
    value: Any


def fields(value: bytes) -> Generator[Field, None, None]:
    i = 0
    while i < len(value):
        num_wire, i = _decode_varint(value, i)
        print(num_wire, i)
        number = num_wire >> 3
        wire_type = num_wire & 0x7

        if wire_type == 0:
            decoded, i = _decode_varint(value, i)
        elif wire_type == 1:
            decoded, i = None, i + 4
        elif wire_type == 2:
            length, i = _decode_varint(value, i)
            decoded = value[i : i + length]
            i += length
        elif wire_type == 5:
            decoded, i = None, i + 2
        else:
            raise NotImplementedError(f"Wire type {wire_type}")

        # print(Field(number=number, wire_type=wire_type, value=decoded))

        yield Field(number=number, wire_type=wire_type, value=decoded)
