from abc import ABC
import json
import struct
from typing import (
    Union,
    Generator,
    Any,
    SupportsBytes,
    List,
    Tuple,
    Callable,
    Type,
    Iterable,
    TypeVar,
)
import dataclasses

from . import parse, serialize

TYPE_ENUM = "enum"
TYPE_BOOL = "bool"
TYPE_INT32 = "int32"
TYPE_INT64 = "int64"
TYPE_UINT32 = "uint32"
TYPE_UINT64 = "uint64"
TYPE_SINT32 = "sint32"
TYPE_SINT64 = "sint64"
TYPE_FLOAT = "float"
TYPE_DOUBLE = "double"
TYPE_FIXED32 = "fixed32"
TYPE_SFIXED32 = "sfixed32"
TYPE_FIXED64 = "fixed64"
TYPE_SFIXED64 = "sfixed64"
TYPE_STRING = "string"
TYPE_BYTES = "bytes"
TYPE_MESSAGE = "message"


FIXED_TYPES = [
    TYPE_FLOAT,
    TYPE_DOUBLE,
    TYPE_FIXED32,
    TYPE_SFIXED32,
    TYPE_FIXED64,
    TYPE_SFIXED64,
]

PACKED_TYPES = [
    TYPE_ENUM,
    TYPE_BOOL,
    TYPE_INT32,
    TYPE_INT64,
    TYPE_UINT32,
    TYPE_UINT64,
    TYPE_SINT32,
    TYPE_SINT64,
    TYPE_FLOAT,
    TYPE_DOUBLE,
    TYPE_FIXED32,
    TYPE_SFIXED32,
    TYPE_FIXED64,
    TYPE_SFIXED64,
]

# Wire types
# https://developers.google.com/protocol-buffers/docs/encoding#structure
WIRE_VARINT = 0
WIRE_FIXED_64 = 1
WIRE_LEN_DELIM = 2
WIRE_FIXED_32 = 5

WIRE_VARINT_TYPES = [
    TYPE_ENUM,
    TYPE_BOOL,
    TYPE_INT32,
    TYPE_INT64,
    TYPE_UINT32,
    TYPE_UINT64,
    TYPE_SINT32,
    TYPE_SINT64,
]

WIRE_FIXED_32_TYPES = [TYPE_FLOAT, TYPE_FIXED32, TYPE_SFIXED32]
WIRE_FIXED_64_TYPES = [TYPE_DOUBLE, TYPE_FIXED64, TYPE_SFIXED64]
WIRE_LEN_DELIM_TYPES = [TYPE_STRING, TYPE_BYTES, TYPE_MESSAGE]


@dataclasses.dataclass(frozen=True)
class _Meta:
    number: int
    proto_type: str
    default: Any


def field(number: int, proto_type: str, default: Any) -> dataclasses.Field:
    kwargs = {}

    if callable(default):
        kwargs["default_factory"] = default
    elif isinstance(default, dict) or isinstance(default, list):
        kwargs["default_factory"] = lambda: default
    else:
        kwargs["default"] = default

    return dataclasses.field(
        **kwargs, metadata={"betterproto": _Meta(number, proto_type, default)}
    )


# Note: the fields below return `Any` to prevent type errors in the generated
# data classes since the types won't match with `Field` and they get swapped
# out at runtime. The generated dataclass variables are still typed correctly.


def enum_field(number: int, default: Union[int, Type[Iterable]] = 0) -> Any:
    return field(number, "enum", default=default)


def int32_field(number: int, default: Union[int, Type[Iterable]] = 0) -> Any:
    return field(number, "int32", default=default)


def int64_field(number: int, default: int = 0) -> Any:
    return field(number, "int64", default=default)


def uint32_field(number: int, default: int = 0) -> Any:
    return field(number, "uint32", default=default)


def uint64_field(number: int, default: int = 0) -> Any:
    return field(number, "uint64", default=default)


def sint32_field(number: int, default: int = 0) -> Any:
    return field(number, "sint32", default=default)


def sint64_field(number: int, default: int = 0) -> Any:
    return field(number, "sint64", default=default)


def float_field(number: int, default: float = 0.0) -> Any:
    return field(number, "float", default=default)


def double_field(number: int, default: float = 0.0) -> Any:
    return field(number, "double", default=default)


def fixed32_field(number: int, default: float = 0.0) -> Any:
    return field(number, "fixed32", default=default)


def fixed64_field(number: int, default: float = 0.0) -> Any:
    return field(number, "fixed64", default=default)


def sfixed32_field(number: int, default: float = 0.0) -> Any:
    return field(number, "sfixed32", default=default)


def sfixed64_field(number: int, default: float = 0.0) -> Any:
    return field(number, "sfixed64", default=default)


def string_field(number: int, default: str = "") -> Any:
    return field(number, "string", default=default)


def message_field(number: int, default: Type["Message"]) -> Any:
    return field(number, "message", default=default)


def _pack_fmt(proto_type: str) -> str:
    return {
        "double": "<d",
        "float": "<f",
        "fixed32": "<I",
        "fixed64": "<Q",
        "sfixed32": "<i",
        "sfixed64": "<q",
    }[proto_type]


def _serialize_single(field_number: int, proto_type: str, value: Any) -> bytes:
    value = _preprocess_single(proto_type, value)

    output = b""
    if proto_type in WIRE_VARINT_TYPES:
        key = serialize._varint(field_number << 3)
        output += key + value
    elif proto_type in WIRE_FIXED_32_TYPES:
        key = serialize._varint((field_number << 3) | 5)
        output += key + value
    elif proto_type in WIRE_FIXED_64_TYPES:
        key = serialize._varint((field_number << 3) | 1)
        output += key + value
    elif proto_type in WIRE_LEN_DELIM_TYPES:
        if len(value):
            key = serialize._varint((field_number << 3) | 2)
            output += key + serialize._varint(len(value)) + value
    else:
        raise NotImplementedError(proto_type)

    return output


def _preprocess_single(proto_type: str, value: Any) -> bytes:
    """Adjusts values before serialization."""
    if proto_type in [
        TYPE_ENUM,
        TYPE_BOOL,
        TYPE_INT32,
        TYPE_INT64,
        TYPE_UINT32,
        TYPE_UINT64,
    ]:
        return serialize._varint(value)
    elif proto_type in [TYPE_SINT32, TYPE_SINT64]:
        # Handle zig-zag encoding.
        if value >= 0:
            value = value << 1
        else:
            value = (value << 1) ^ (~0)
        return serialize._varint(value)
    elif proto_type in FIXED_TYPES:
        return struct.pack(_pack_fmt(proto_type), value)
    elif proto_type == TYPE_STRING:
        return value.encode("utf-8")
    elif proto_type == TYPE_MESSAGE:
        return bytes(value)

    return value


def _postprocess_single(wire_type: int, meta: _Meta, field: Any, value: Any) -> Any:
    """Adjusts values after parsing."""
    if wire_type == WIRE_VARINT:
        if meta.proto_type in ["int32", "int64"]:
            bits = int(meta.proto_type[3:])
            value = value & ((1 << bits) - 1)
            signbit = 1 << (bits - 1)
            value = int((value ^ signbit) - signbit)
        elif meta.proto_type in ["sint32", "sint64"]:
            # Undo zig-zag encoding
            value = (value >> 1) ^ (-(value & 1))
    elif wire_type in [WIRE_FIXED_32, WIRE_FIXED_64]:
        fmt = _pack_fmt(meta.proto_type)
        value = struct.unpack(fmt, value)[0]
    elif wire_type == WIRE_LEN_DELIM:
        if meta.proto_type in ["string"]:
            value = value.decode("utf-8")
        elif meta.proto_type in ["message"]:
            value = field.default_factory().parse(value)

    return value


# Bound type variable to allow methods to return `self` of subclasses
T = TypeVar("T", bound="Message")


class Message(ABC):
    """
    A protobuf message base class. Generated code will inherit from this and
    register the message fields which get used by the serializers and parsers
    to go between Python, binary and JSON protobuf message representations.
    """

    def __bytes__(self) -> bytes:
        """
        Get the binary encoded Protobuf representation of this instance.
        """
        output = b""
        for field in dataclasses.fields(self):
            meta: _Meta = field.metadata.get("betterproto")
            value = getattr(self, field.name)

            if isinstance(value, list):
                if not len(value):
                    continue

                if meta.proto_type in PACKED_TYPES:
                    # Packed lists look like a length-delimited field. First,
                    # preprocess/encode each value into a buffer and then
                    # treat it like a field of raw bytes.
                    buf = b""
                    for item in value:
                        buf += _preprocess_single(meta.proto_type, item)
                    output += _serialize_single(meta.number, TYPE_BYTES, buf)
                else:
                    for item in value:
                        output += _serialize_single(meta.number, meta.proto_type, item)
            else:
                if value == field.default:
                    continue

                output += _serialize_single(meta.number, meta.proto_type, value)

        return output

    def parse(self, data: bytes) -> T:
        """
        Parse the binary encoded Protobuf into this message instance. This
        returns the instance itself and is therefore assignable and chainable.
        """
        fields = {f.metadata["betterproto"].number: f for f in dataclasses.fields(self)}
        for parsed in parse.fields(data):
            if parsed.number in fields:
                field = fields[parsed.number]
                meta: _Meta = field.metadata.get("betterproto")

                if (
                    parsed.wire_type == WIRE_LEN_DELIM
                    and meta.proto_type in PACKED_TYPES
                ):
                    # This is a packed repeated field.
                    pos = 0
                    value = []
                    while pos < len(parsed.value):
                        if meta.proto_type in ["float", "fixed32", "sfixed32"]:
                            decoded, pos = parsed.value[pos : pos + 4], pos + 4
                            wire_type = WIRE_FIXED_32
                        elif meta.proto_type in ["double", "fixed64", "sfixed64"]:
                            decoded, pos = parsed.value[pos : pos + 8], pos + 8
                            wire_type = WIRE_FIXED_64
                        else:
                            decoded, pos = parse.parse_varint(parsed.value, pos)
                            wire_type = WIRE_VARINT
                        decoded = _postprocess_single(wire_type, meta, field, decoded)
                        value.append(decoded)
                else:
                    value = _postprocess_single(
                        parsed.wire_type, meta, field, parsed.value
                    )

                if isinstance(getattr(self, field.name), list) and not isinstance(
                    value, list
                ):
                    getattr(self, field.name).append(value)
                else:
                    setattr(self, field.name, value)
            else:
                # TODO: handle unknown fields
                pass

        return self

    def to_dict(self) -> dict:
        """
        Returns a dict representation of this message instance which can be
        used to serialize to e.g. JSON.
        """
        output = {}
        for field in dataclasses.fields(self):
            meta: Meta_ = field.metadata.get("betterproto")
            v = getattr(self, field.name)
            if meta.proto_type == "message":
                v = v.to_dict()
                if v:
                    output[field.name] = v
            elif v != field.default:
                output[field.name] = getattr(self, field.name)
        return output

    def from_dict(self, value: dict) -> T:
        """
        Parse the key/value pairs in `value` into this message instance. This
        returns the instance itself and is therefore assignable and chainable.
        """
        for field in dataclasses.fields(self):
            meta: Meta_ = field.metadata.get("betterproto")
            if field.name in value:
                if meta.proto_type == "message":
                    getattr(self, field.name).from_dict(value[field.name])
                else:
                    setattr(self, field.name, value[field.name])
        return self

    def to_json(self) -> bytes:
        """Returns the encoded JSON representation of this message instance."""
        return json.dumps(self.to_dict())

    def from_json(self, value: bytes) -> T:
        """
        Parse the key/value pairs in `value` into this message instance. This
        returns the instance itself and is therefore assignable and chainable.
        """
        return self.from_dict(json.loads(value))
