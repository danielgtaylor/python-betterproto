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

PACKED_TYPES = [
    "bool",
    "int32",
    "int64",
    "uint32",
    "uint64",
    "sint32",
    "sint64",
    "float",
    "double",
]

# Wire types
# https://developers.google.com/protocol-buffers/docs/encoding#structure
WIRE_VARINT = 0
WIRE_FIXED_64 = 1
WIRE_LEN_DELIM = 2
WIRE_FIXED_32 = 5


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


def int32_field(
    number: int, default: Union[int, Type[Iterable]] = 0
) -> dataclasses.Field:
    return field(number, "int32", default=default)


def int64_field(number: int, default: int = 0) -> dataclasses.Field:
    return field(number, "int64", default=default)


def uint32_field(number: int, default: int = 0) -> dataclasses.Field:
    return field(number, "uint32", default=default)


def uint64_field(number: int, default: int = 0) -> dataclasses.Field:
    return field(number, "uint64", default=default)


def sint32_field(number: int, default: int = 0) -> dataclasses.Field:
    return field(number, "sint32", default=default)


def sint64_field(number: int, default: int = 0) -> dataclasses.Field:
    return field(number, "sint64", default=default)


def float_field(number: int, default: float = 0.0) -> dataclasses.Field:
    return field(number, "float", default=default)


def double_field(number: int, default: float = 0.0) -> dataclasses.Field:
    return field(number, "double", default=default)


def string_field(number: int, default: str = "") -> dataclasses.Field:
    return field(number, "string", default=default)


def message_field(number: int, default: Type["ProtoMessage"]) -> dataclasses.Field:
    return field(number, "message", default=default)


def _serialize_single(meta: _Meta, value: Any) -> bytes:
    output = b""
    if meta.proto_type in ["int32", "int64", "uint32", "uint64"]:
        if value < 0:
            # Handle negative numbers.
            value += 1 << 64
        output = serialize.varint(meta.number, value)
    elif meta.proto_type in ["sint32", "sint64"]:
        if value >= 0:
            value = value << 1
        else:
            value = (value << 1) ^ (~0)
        output = serialize.varint(meta.number, value)
    elif meta.proto_type == "string":
        output = serialize.len_delim(meta.number, value.encode("utf-8"))
    elif meta.proto_type == "message":
        b = bytes(value)
        if len(b):
            output = serialize.len_delim(meta.number, b)
    else:
        raise NotImplementedError()

    return output


def _parse_single(wire_type: int, meta: _Meta, field: Any, value: Any) -> Any:
    if wire_type == WIRE_VARINT:
        if meta.proto_type in ["int32", "int64"]:
            bits = int(meta.proto_type[3:])
            value = value & ((1 << bits) - 1)
            signbit = 1 << (bits - 1)
            value = int((value ^ signbit) - signbit)
        elif meta.proto_type in ["sint32", "sint64"]:
            # Undo zig-zag encoding
            value = (value >> 1) ^ (-(value & 1))
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
                    output += serialize.packed(meta.number, value)
                else:
                    for item in value:
                        output += _serialize_single(meta, item)
            else:
                if value == field.default:
                    continue

                output += _serialize_single(meta, value)

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
                        decoded, pos = parse._decode_varint(parsed.value, pos)
                        decoded = _parse_single(WIRE_VARINT, meta, field, decoded)
                        value.append(decoded)
                else:
                    value = _parse_single(parsed.wire_type, meta, field, parsed.value)

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
