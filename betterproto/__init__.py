from abc import ABC
import json
import struct
from typing import (
    get_type_hints,
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
    Optional,
)
import dataclasses

import inspect

# Proto 3 data types
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
TYPE_MAP = "map"


# Fields that use a fixed amount of space (4 or 8 bytes)
FIXED_TYPES = [
    TYPE_FLOAT,
    TYPE_DOUBLE,
    TYPE_FIXED32,
    TYPE_SFIXED32,
    TYPE_FIXED64,
    TYPE_SFIXED64,
]

# Fields that are efficiently packed when
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

# Mappings of which Proto 3 types correspond to which wire types.
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
WIRE_LEN_DELIM_TYPES = [TYPE_STRING, TYPE_BYTES, TYPE_MESSAGE, TYPE_MAP]


@dataclasses.dataclass(frozen=True)
class FieldMetadata:
    """Stores internal metadata used for parsing & serialization."""

    # Protobuf field number
    number: int
    # Protobuf type name
    proto_type: str
    # Map information if the proto_type is a map
    map_types: Optional[Tuple[str, str]]
    # Default value if given
    default: Any

    @staticmethod
    def get(field: dataclasses.Field) -> "FieldMetadata":
        """Returns the field metadata for a dataclass field."""
        return field.metadata["betterproto"]


def dataclass_field(
    number: int,
    proto_type: str,
    default: Any,
    map_types: Optional[Tuple[str, str]] = None,
    **kwargs: dict,
) -> dataclasses.Field:
    """Creates a dataclass field with attached protobuf metadata."""
    if callable(default):
        kwargs["default_factory"] = default
    elif isinstance(default, dict) or isinstance(default, list):
        kwargs["default_factory"] = lambda: default
    else:
        kwargs["default"] = default

    return dataclasses.field(
        **kwargs,
        metadata={"betterproto": FieldMetadata(number, proto_type, map_types, default)},
    )


# Note: the fields below return `Any` to prevent type errors in the generated
# data classes since the types won't match with `Field` and they get swapped
# out at runtime. The generated dataclass variables are still typed correctly.


def enum_field(number: int, default: Union[int, Type[Iterable]] = 0) -> Any:
    return dataclass_field(number, TYPE_ENUM, default=default)


def int32_field(number: int, default: Union[int, Type[Iterable]] = 0) -> Any:
    return dataclass_field(number, TYPE_INT32, default=default)


def int64_field(number: int, default: int = 0) -> Any:
    return dataclass_field(number, TYPE_INT64, default=default)


def uint32_field(number: int, default: int = 0) -> Any:
    return dataclass_field(number, TYPE_UINT32, default=default)


def uint64_field(number: int, default: int = 0) -> Any:
    return dataclass_field(number, TYPE_UINT64, default=default)


def sint32_field(number: int, default: int = 0) -> Any:
    return dataclass_field(number, TYPE_SINT32, default=default)


def sint64_field(number: int, default: int = 0) -> Any:
    return dataclass_field(number, TYPE_SINT64, default=default)


def float_field(number: int, default: float = 0.0) -> Any:
    return dataclass_field(number, TYPE_FLOAT, default=default)


def double_field(number: int, default: float = 0.0) -> Any:
    return dataclass_field(number, TYPE_DOUBLE, default=default)


def fixed32_field(number: int, default: float = 0.0) -> Any:
    return dataclass_field(number, TYPE_FIXED32, default=default)


def fixed64_field(number: int, default: float = 0.0) -> Any:
    return dataclass_field(number, TYPE_FIXED64, default=default)


def sfixed32_field(number: int, default: float = 0.0) -> Any:
    return dataclass_field(number, TYPE_SFIXED32, default=default)


def sfixed64_field(number: int, default: float = 0.0) -> Any:
    return dataclass_field(number, TYPE_SFIXED64, default=default)


def string_field(number: int, default: str = "") -> Any:
    return dataclass_field(number, TYPE_STRING, default=default)


def message_field(number: int, default: Type["Message"]) -> Any:
    return dataclass_field(number, TYPE_MESSAGE, default=default)


def map_field(number: int, key_type: str, value_type: str) -> Any:
    return dataclass_field(
        number, TYPE_MAP, default=dict, map_types=(key_type, value_type)
    )


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
        return encode_varint(value)
    elif proto_type in [TYPE_SINT32, TYPE_SINT64]:
        # Handle zig-zag encoding.
        if value >= 0:
            value = value << 1
        else:
            value = (value << 1) ^ (~0)
        return encode_varint(value)
    elif proto_type in FIXED_TYPES:
        return struct.pack(_pack_fmt(proto_type), value)
    elif proto_type == TYPE_STRING:
        return value.encode("utf-8")
    elif proto_type == TYPE_MESSAGE:
        return bytes(value)

    return value


def _serialize_single(field_number: int, proto_type: str, value: Any) -> bytes:
    """Serializes a single field and value."""
    value = _preprocess_single(proto_type, value)

    output = b""
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
        if len(value):
            key = encode_varint((field_number << 3) | 2)
            output += key + encode_varint(len(value)) + value
    else:
        raise NotImplementedError(proto_type)

    return output


def decode_varint(buffer: bytes, pos: int, signed: bool = False) -> Tuple[int, int]:
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
            return (result, pos)
        shift += 7
        if shift >= 64:
            raise ValueError("Too many bytes when decoding varint.")


@dataclasses.dataclass(frozen=True)
class ParsedField:
    number: int
    wire_type: int
    value: Any


def parse_fields(value: bytes) -> Generator[ParsedField, None, None]:
    i = 0
    while i < len(value):
        num_wire, i = decode_varint(value, i)
        # print(num_wire, i)
        number = num_wire >> 3
        wire_type = num_wire & 0x7

        if wire_type == 0:
            decoded, i = decode_varint(value, i)
        elif wire_type == 1:
            decoded, i = value[i : i + 8], i + 8
        elif wire_type == 2:
            length, i = decode_varint(value, i)
            decoded = value[i : i + length]
            i += length
        elif wire_type == 5:
            decoded, i = value[i : i + 4], i + 4
        else:
            raise NotImplementedError(f"Wire type {wire_type}")

        # print(ParsedField(number=number, wire_type=wire_type, value=decoded))

        yield ParsedField(number=number, wire_type=wire_type, value=decoded)


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
            meta = FieldMetadata.get(field)
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
            elif isinstance(value, dict):
                if not len(value):
                    continue

                for k, v in value.items():
                    sk = _serialize_single(1, meta.map_types[0], k)
                    sv = _serialize_single(2, meta.map_types[1], v)
                    output += _serialize_single(meta.number, meta.proto_type, sk + sv)
            else:
                if value == field.default:
                    continue

                output += _serialize_single(meta.number, meta.proto_type, value)

        return output

    def _cls_for(self, field: dataclasses.Field) -> Type:
        """Get the message class for a field from the type hints."""
        module = inspect.getmodule(self)
        type_hints = get_type_hints(self, vars(module))
        cls = type_hints[field.name]
        if hasattr(cls, "__args__"):
            print(type_hints[field.name].__args__[0])
            cls = type_hints[field.name].__args__[0]
        return cls

    def _postprocess_single(
        self, wire_type: int, meta: FieldMetadata, field: dataclasses.Field, value: Any
    ) -> Any:
        """Adjusts values after parsing."""
        if wire_type == WIRE_VARINT:
            if meta.proto_type in [TYPE_INT32, TYPE_INT64]:
                bits = int(meta.proto_type[3:])
                value = value & ((1 << bits) - 1)
                signbit = 1 << (bits - 1)
                value = int((value ^ signbit) - signbit)
            elif meta.proto_type in [TYPE_SINT32, TYPE_SINT64]:
                # Undo zig-zag encoding
                value = (value >> 1) ^ (-(value & 1))
        elif wire_type in [WIRE_FIXED_32, WIRE_FIXED_64]:
            fmt = _pack_fmt(meta.proto_type)
            value = struct.unpack(fmt, value)[0]
        elif wire_type == WIRE_LEN_DELIM:
            if meta.proto_type in [TYPE_STRING]:
                value = value.decode("utf-8")
            elif meta.proto_type in [TYPE_MESSAGE]:
                cls = self._cls_for(field)
                value = cls().parse(value)
            elif meta.proto_type in [TYPE_MAP]:
                # TODO: This is slow, use a cache to make it faster since each
                #       key/value pair will recreate the class.
                Entry = dataclasses.make_dataclass(
                    "Entry",
                    [
                        ("key", Any, dataclass_field(1, meta.map_types[0], None)),
                        ("value", Any, dataclass_field(2, meta.map_types[1], None)),
                    ],
                    bases=(Message,),
                )
                value = Entry().parse(value)

        return value

    def parse(self, data: bytes) -> T:
        """
        Parse the binary encoded Protobuf into this message instance. This
        returns the instance itself and is therefore assignable and chainable.
        """
        fields = {f.metadata["betterproto"].number: f for f in dataclasses.fields(self)}
        for parsed in parse_fields(data):
            if parsed.number in fields:
                field = fields[parsed.number]
                meta = FieldMetadata.get(field)

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
                            decoded, pos = decode_varint(parsed.value, pos)
                            wire_type = WIRE_VARINT
                        decoded = self._postprocess_single(
                            wire_type, meta, field, decoded
                        )
                        value.append(decoded)
                else:
                    value = self._postprocess_single(
                        parsed.wire_type, meta, field, parsed.value
                    )

                current = getattr(self, field.name)
                if meta.proto_type == TYPE_MAP:
                    # Value represents a single key/value pair entry in the map.
                    current[value.key] = value.value
                elif isinstance(current, list) and not isinstance(value, list):
                    current.append(value)
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
            meta = FieldMetadata.get(field)
            v = getattr(self, field.name)
            if meta.proto_type == "message":
                if isinstance(v, list):
                    # Convert each item.
                    v = [i.to_dict() for i in v]
                    # Filter out empty items which we won't serialize.
                    v = [i for i in v if i]
                else:
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
            meta = FieldMetadata.get(field)
            if field.name in value:
                if meta.proto_type == "message":
                    v = getattr(self, field.name)
                    print(v, value[field.name])
                    if isinstance(v, list):
                        cls = self._cls_for(field)
                        for i in range(len(value[field.name])):
                            v.append(cls().from_dict(value[field.name][i]))
                    else:
                        v.from_dict(value[field.name])
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
