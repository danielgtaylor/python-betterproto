import dataclasses
from datetime import timedelta
import struct
from typing import Any, List, Union, Tuple

from typing import Generator

from .message import _Duration, _Timestamp, _get_wrapper
from .const import *


def _pack_fmt(proto_type: str) -> str:
    """Returns a little-endian format string for reading/writing binary."""
    return {
        TYPE_DOUBLE: "<d",
        TYPE_FLOAT: "<f",
        TYPE_FIXED32: "<I",
        TYPE_FIXED64: "<Q",
        TYPE_SFIXED32: "<i",
        TYPE_SFIXED64: "<q",
    }[proto_type]


def encode_varint(value: int) -> bytes:
    """Encodes a single varint value for serialization."""
    b: List[int] = []

    if value < 0:
        value += 1 << 64

    bits = value & 0x7F
    value >>= 7
    while value:
        b.append(0x80 | bits)
        bits = value & 0x7F
        value >>= 7
    return bytes(b + [bits])


def _preprocess_single(proto_type: str, wraps: str, value: Any) -> bytes:
    """Adjusts values before serialization."""
    if proto_type in (
        TYPE_ENUM,
        TYPE_BOOL,
        TYPE_INT32,
        TYPE_INT64,
        TYPE_UINT32,
        TYPE_UINT64,
    ):
        return encode_varint(value)
    elif proto_type in (TYPE_SINT32, TYPE_SINT64):
        # Handle zig-zag encoding.
        return encode_varint(value << 1 if value >= 0 else (value << 1) ^ (~0))
    elif proto_type in FIXED_TYPES:
        return struct.pack(_pack_fmt(proto_type), value)
    elif proto_type == TYPE_STRING:
        return value.encode("utf-8")
    elif proto_type == TYPE_MESSAGE:
        if isinstance(value, datetime):
            # Convert the `datetime` to a timestamp message.
            seconds = int(value.timestamp())
            nanos = int(value.microsecond * 1e3)
            value = _Timestamp(seconds=seconds, nanos=nanos)
        elif isinstance(value, timedelta):
            # Convert the `timedelta` to a duration message.
            total_ms = value // timedelta(microseconds=1)
            seconds = int(total_ms / 1e6)
            nanos = int((total_ms % 1e6) * 1e3)
            value = _Duration(seconds=seconds, nanos=nanos)
        elif wraps:
            if value is None:
                return b""
            value = _get_wrapper(wraps)(value=value)

        return bytes(value)

    return value


def _serialize_single(
    field_number: int,
    proto_type: str,
    value: Any,
    *,
    serialize_empty: bool = False,
    wraps: str = "",
) -> bytes:
    """Serializes a single field and value."""
    value = _preprocess_single(proto_type, wraps, value)

    output = bytearray()
    if proto_type in WIRE_VARINT_TYPES:
        key = encode_varint(field_number << 3)
        output += key + value
    elif proto_type in WIRE_FIXED_32_TYPES:
        key = encode_varint((field_number << 3) | 5)
        output += key + value
    elif proto_type in WIRE_FIXED_64_TYPES:
        key = encode_varint((field_number << 3) | 1)
        output += key + value
    elif proto_type in WIRE_LEN_DELIM_TYPES:
        if len(value) or serialize_empty or wraps:
            key = encode_varint((field_number << 3) | 2)
            output += key + encode_varint(len(value)) + value
    else:
        raise NotImplementedError(proto_type)

    return bytes(output)


def _parse_float(value: Any) -> float:
    """Parse the given value to a float

    Parameters
    ----------
    value : Any
        Value to parse

    Returns
    -------
    float
        Parsed value
    """
    if value == INFINITY:
        return float("inf")
    if value == NEG_INFINITY:
        return -float("inf")
    if value == NAN:
        return float("nan")
    return float(value)


def _dump_float(value: float) -> Union[float, str]:
    """Dump the given float to JSON

    Parameters
    ----------
    value : float
        Value to dump

    Returns
    -------
    Union[float, str]
        Dumped valid, either a float or the strings
        "Infinity" or "-Infinity"
    """
    if value == float("inf"):
        return INFINITY
    if value == -float("inf"):
        return NEG_INFINITY
    if value == float("nan"):
        return NAN
    return value


def decode_varint(buffer: bytes, pos: int) -> Tuple[int, int]:
    """
    Decode a single varint value from a byte buffer. Returns the value and the
    new position in the buffer.
    """
    result = 0
    shift = 0
    while 1:
        b = buffer[pos]
        result |= (b & 0x7F) << shift
        pos += 1
        if not (b & 0x80):
            return result, pos
        shift += 7
        if shift >= 64:
            raise ValueError("Too many bytes when decoding varint.")


@dataclasses.dataclass(frozen=True)
class ParsedField:
    number: int
    wire_type: int
    value: Any
    raw: bytes


def parse_fields(value: bytes) -> Generator[ParsedField, None, None]:
    i = 0
    while i < len(value):
        start = i
        num_wire, i = decode_varint(value, i)
        number = num_wire >> 3
        wire_type = num_wire & 0x7

        decoded: Any = None
        if wire_type == WIRE_VARINT:
            decoded, i = decode_varint(value, i)
        elif wire_type == WIRE_FIXED_64:
            decoded, i = value[i : i + 8], i + 8
        elif wire_type == WIRE_LEN_DELIM:
            length, i = decode_varint(value, i)
            decoded = value[i : i + length]
            i += length
        elif wire_type == WIRE_FIXED_32:
            decoded, i = value[i : i + 4], i + 4

        yield ParsedField(
            number=number, wire_type=wire_type, value=decoded, raw=value[start:i]
        )
