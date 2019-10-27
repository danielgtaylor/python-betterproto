import dataclasses
import enum
import inspect
import json
import struct
from abc import ABC
from base64 import b64encode, b64decode
from datetime import datetime, timedelta, timezone
from typing import (
    Any,
    AsyncGenerator,
    Callable,
    Dict,
    Generator,
    Iterable,
    List,
    Optional,
    SupportsBytes,
    Tuple,
    Type,
    TypeVar,
    Union,
    get_type_hints,
)

import grpclib.client
import grpclib.const
import stringcase

from .casing import safe_snake_case

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

# Fields that are numerical 64-bit types
INT_64_TYPES = [TYPE_INT64, TYPE_UINT64, TYPE_SINT64, TYPE_FIXED64, TYPE_SFIXED64]

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


# Protobuf datetimes start at the Unix Epoch in 1970 in UTC.
DATETIME_ZERO = datetime(1970, 1, 1, tzinfo=timezone.utc)


class Casing(enum.Enum):
    """Casing constants for serialization."""

    CAMEL = stringcase.camelcase
    SNAKE = stringcase.snakecase


class _PLACEHOLDER:
    pass


PLACEHOLDER: Any = _PLACEHOLDER()


@dataclasses.dataclass(frozen=True)
class FieldMetadata:
    """Stores internal metadata used for parsing & serialization."""

    # Protobuf field number
    number: int
    # Protobuf type name
    proto_type: str
    # Map information if the proto_type is a map
    map_types: Optional[Tuple[str, str]] = None
    # Groups several "one-of" fields together
    group: Optional[str] = None
    # Describes the wrapped type (e.g. when using google.protobuf.BoolValue)
    wraps: Optional[str] = None

    @staticmethod
    def get(field: dataclasses.Field) -> "FieldMetadata":
        """Returns the field metadata for a dataclass field."""
        return field.metadata["betterproto"]


def dataclass_field(
    number: int,
    proto_type: str,
    *,
    map_types: Optional[Tuple[str, str]] = None,
    group: Optional[str] = None,
    wraps: Optional[str] = None,
) -> dataclasses.Field:
    """Creates a dataclass field with attached protobuf metadata."""
    return dataclasses.field(
        default=PLACEHOLDER,
        metadata={
            "betterproto": FieldMetadata(number, proto_type, map_types, group, wraps)
        },
    )


# Note: the fields below return `Any` to prevent type errors in the generated
# data classes since the types won't match with `Field` and they get swapped
# out at runtime. The generated dataclass variables are still typed correctly.


def enum_field(number: int, group: Optional[str] = None) -> Any:
    return dataclass_field(number, TYPE_ENUM, group=group)


def bool_field(number: int, group: Optional[str] = None) -> Any:
    return dataclass_field(number, TYPE_BOOL, group=group)


def int32_field(number: int, group: Optional[str] = None) -> Any:
    return dataclass_field(number, TYPE_INT32, group=group)


def int64_field(number: int, group: Optional[str] = None) -> Any:
    return dataclass_field(number, TYPE_INT64, group=group)


def uint32_field(number: int, group: Optional[str] = None) -> Any:
    return dataclass_field(number, TYPE_UINT32, group=group)


def uint64_field(number: int, group: Optional[str] = None) -> Any:
    return dataclass_field(number, TYPE_UINT64, group=group)


def sint32_field(number: int, group: Optional[str] = None) -> Any:
    return dataclass_field(number, TYPE_SINT32, group=group)


def sint64_field(number: int, group: Optional[str] = None) -> Any:
    return dataclass_field(number, TYPE_SINT64, group=group)


def float_field(number: int, group: Optional[str] = None) -> Any:
    return dataclass_field(number, TYPE_FLOAT, group=group)


def double_field(number: int, group: Optional[str] = None) -> Any:
    return dataclass_field(number, TYPE_DOUBLE, group=group)


def fixed32_field(number: int, group: Optional[str] = None) -> Any:
    return dataclass_field(number, TYPE_FIXED32, group=group)


def fixed64_field(number: int, group: Optional[str] = None) -> Any:
    return dataclass_field(number, TYPE_FIXED64, group=group)


def sfixed32_field(number: int, group: Optional[str] = None) -> Any:
    return dataclass_field(number, TYPE_SFIXED32, group=group)


def sfixed64_field(number: int, group: Optional[str] = None) -> Any:
    return dataclass_field(number, TYPE_SFIXED64, group=group)


def string_field(number: int, group: Optional[str] = None) -> Any:
    return dataclass_field(number, TYPE_STRING, group=group)


def bytes_field(number: int, group: Optional[str] = None) -> Any:
    return dataclass_field(number, TYPE_BYTES, group=group)


def message_field(
    number: int, group: Optional[str] = None, wraps: Optional[str] = None
) -> Any:
    return dataclass_field(number, TYPE_MESSAGE, group=group, wraps=wraps)


def map_field(
    number: int, key_type: str, value_type: str, group: Optional[str] = None
) -> Any:
    return dataclass_field(
        number, TYPE_MAP, map_types=(key_type, value_type), group=group
    )


class Enum(int, enum.Enum):
    """Protocol buffers enumeration base class. Acts like `enum.IntEnum`."""

    @classmethod
    def from_string(cls, name: str) -> int:
        """Return the value which corresponds to the string name."""
        try:
            return cls.__members__[name]
        except KeyError as e:
            raise ValueError(f"Unknown value {name} for enum {cls.__name__}") from e


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
        if len(value) or serialize_empty or wraps:
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
    raw: bytes


def parse_fields(value: bytes) -> Generator[ParsedField, None, None]:
    i = 0
    while i < len(value):
        start = i
        num_wire, i = decode_varint(value, i)
        number = num_wire >> 3
        wire_type = num_wire & 0x7

        decoded: Any = None
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

        yield ParsedField(
            number=number, wire_type=wire_type, value=decoded, raw=value[start:i]
        )


# Bound type variable to allow methods to return `self` of subclasses
T = TypeVar("T", bound="Message")


class Message(ABC):
    """
    A protobuf message base class. Generated code will inherit from this and
    register the message fields which get used by the serializers and parsers
    to go between Python, binary and JSON protobuf message representations.
    """
    _serialized_on_wire: bool
    _unknown_fields: bytes
    _group_map: Dict[str, dict]

    def __post_init__(self) -> None:
        # Set a default value for each field in the class after `__init__` has
        # already been run.
        group_map: Dict[str, dict] = {"fields": {}, "groups": {}}
        for field in dataclasses.fields(self):
            meta = FieldMetadata.get(field)

            if meta.group:
                # This is part of a one-of group.
                group_map["fields"][field.name] = meta.group

                if meta.group not in group_map["groups"]:
                    group_map["groups"][meta.group] = {"current": None, "fields": set()}
                group_map["groups"][meta.group]["fields"].add(field)

            if getattr(self, field.name) != PLACEHOLDER:
                # Skip anything not set to the sentinel value

                if meta.group:
                    # This was set, so make it the selected value of the one-of.
                    group_map["groups"][meta.group]["current"] = field

                continue

            setattr(self, field.name, self._get_field_default(field, meta))

        # Now that all the defaults are set, reset it!
        self.__dict__["_serialized_on_wire"] = False
        self.__dict__["_unknown_fields"] = b""
        self.__dict__["_group_map"] = group_map

    def __setattr__(self, attr: str, value: Any) -> None:
        if attr != "_serialized_on_wire":
            # Track when a field has been set.
            self.__dict__["_serialized_on_wire"] = True

        if attr in getattr(self, "_group_map", {}).get("fields", {}):
            group = self._group_map["fields"][attr]
            for field in self._group_map["groups"][group]["fields"]:
                if field.name == attr:
                    self._group_map["groups"][group]["current"] = field
                else:
                    super().__setattr__(
                        field.name,
                        self._get_field_default(field, FieldMetadata.get(field)),
                    )

        super().__setattr__(attr, value)

    def __bytes__(self) -> bytes:
        """
        Get the binary encoded Protobuf representation of this instance.
        """
        output = b""
        for field in dataclasses.fields(self):
            meta = FieldMetadata.get(field)
            value = getattr(self, field.name)

            if value is None:
                # Optional items should be skipped. This is used for the Google
                # wrapper types.
                continue

            # Being selected in a a group means this field is the one that is
            # currently set in a `oneof` group, so it must be serialized even
            # if the value is the default zero value.
            selected_in_group = False
            if meta.group and self._group_map["groups"][meta.group]["current"] == field:
                selected_in_group = True

            serialize_empty = False
            if isinstance(value, Message) and value._serialized_on_wire:
                # Empty messages can still be sent on the wire if they were
                # set (or received empty).
                serialize_empty = True

            if value == self._get_field_default(field, meta) and not (
                selected_in_group or serialize_empty
            ):
                # Default (zero) values are not serialized. Two exceptions are
                # if this is the selected oneof item or if we know we have to
                # serialize an empty message (i.e. zero value was explicitly
                # set by the user).
                continue

            if isinstance(value, list):
                if meta.proto_type in PACKED_TYPES:
                    # Packed lists look like a length-delimited field. First,
                    # preprocess/encode each value into a buffer and then
                    # treat it like a field of raw bytes.
                    buf = b""
                    for item in value:
                        buf += _preprocess_single(meta.proto_type, "", item)
                    output += _serialize_single(meta.number, TYPE_BYTES, buf)
                else:
                    for item in value:
                        output += _serialize_single(
                            meta.number, meta.proto_type, item, wraps=meta.wraps or ""
                        )
            elif isinstance(value, dict):
                for k, v in value.items():
                    assert meta.map_types
                    sk = _serialize_single(1, meta.map_types[0], k)
                    sv = _serialize_single(2, meta.map_types[1], v)
                    output += _serialize_single(meta.number, meta.proto_type, sk + sv)
            else:
                output += _serialize_single(
                    meta.number,
                    meta.proto_type,
                    value,
                    serialize_empty=serialize_empty,
                    wraps=meta.wraps or "",
                )

        return output + self._unknown_fields

    # For compatibility with other libraries
    SerializeToString = __bytes__

    def _type_hint(self, field_name: str) -> Type:
        module = inspect.getmodule(self.__class__)
        type_hints = get_type_hints(self.__class__, vars(module))
        return type_hints[field_name]

    def _cls_for(self, field: dataclasses.Field, index: int = 0) -> Type:
        """Get the message class for a field from the type hints."""
        cls = self._type_hint(field.name)
        if hasattr(cls, "__args__") and index >= 0:
            cls = cls.__args__[index]
        return cls

    def _get_field_default(self, field: dataclasses.Field, meta: FieldMetadata) -> Any:
        t = self._type_hint(field.name)

        value: Any = 0
        if hasattr(t, "__origin__"):
            if t.__origin__ == dict:
                # This is some kind of map (dict in Python).
                value = {}
            elif t.__origin__ == list:
                # This is some kind of list (repeated) field.
                value = []
            elif t.__origin__ == Union and t.__args__[1] == type(None):
                # This is an optional (wrapped) field. For setting the default we
                # really don't care what kind of field it is.
                value = None
            else:
                value = t()
        elif issubclass(t, Enum):
            # Enums always default to zero.
            value = 0
        elif t == datetime:
            # Offsets are relative to 1970-01-01T00:00:00Z
            value = DATETIME_ZERO
        else:
            # This is either a primitive scalar or another message type. Calling
            # it should result in its zero value.
            value = t()

        return value

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
            elif meta.proto_type == TYPE_BOOL:
                # Booleans use a varint encoding, so convert it to true/false.
                value = value > 0
        elif wire_type in [WIRE_FIXED_32, WIRE_FIXED_64]:
            fmt = _pack_fmt(meta.proto_type)
            value = struct.unpack(fmt, value)[0]
        elif wire_type == WIRE_LEN_DELIM:
            if meta.proto_type == TYPE_STRING:
                value = value.decode("utf-8")
            elif meta.proto_type == TYPE_MESSAGE:
                cls = self._cls_for(field)

                if cls == datetime:
                    value = _Timestamp().parse(value).to_datetime()
                elif cls == timedelta:
                    value = _Duration().parse(value).to_timedelta()
                elif meta.wraps:
                    # This is a Google wrapper value message around a single
                    # scalar type.
                    value = _get_wrapper(meta.wraps)().parse(value).value
                else:
                    value = cls().parse(value)
                    value._serialized_on_wire = True
            elif meta.proto_type == TYPE_MAP:
                # TODO: This is slow, use a cache to make it faster since each
                #       key/value pair will recreate the class.
                assert meta.map_types
                kt = self._cls_for(field, index=0)
                vt = self._cls_for(field, index=1)
                Entry = dataclasses.make_dataclass(
                    "Entry",
                    [
                        ("key", kt, dataclass_field(1, meta.map_types[0])),
                        ("value", vt, dataclass_field(2, meta.map_types[1])),
                    ],
                    bases=(Message,),
                )
                value = Entry().parse(value)

        return value

    def parse(self: T, data: bytes) -> T:
        """
        Parse the binary encoded Protobuf into this message instance. This
        returns the instance itself and is therefore assignable and chainable.
        """
        fields = {f.metadata["betterproto"].number: f for f in dataclasses.fields(self)}
        for parsed in parse_fields(data):
            if parsed.number in fields:
                field = fields[parsed.number]
                meta = FieldMetadata.get(field)

                value: Any
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
                self._unknown_fields += parsed.raw

        return self

    # For compatibility with other libraries.
    @classmethod
    def FromString(cls: Type[T], data: bytes) -> T:
        return cls().parse(data)

    def to_dict(self, casing: Casing = Casing.CAMEL) -> dict:
        """
        Returns a dict representation of this message instance which can be
        used to serialize to e.g. JSON. Defaults to camel casing for
        compatibility but can be set to other modes.
        """
        output: Dict[str, Any] = {}
        for field in dataclasses.fields(self):
            meta = FieldMetadata.get(field)
            v = getattr(self, field.name)
            cased_name = casing(field.name).rstrip("_") # type: ignore
            if meta.proto_type == "message":
                if isinstance(v, datetime):
                    if v != DATETIME_ZERO:
                        output[cased_name] = _Timestamp.timestamp_to_json(v)
                elif isinstance(v, timedelta):
                    if v != timedelta(0):
                        output[cased_name] = _Duration.delta_to_json(v)
                elif meta.wraps:
                    if v is not None:
                        output[cased_name] = v
                elif isinstance(v, list):
                    # Convert each item.
                    v = [i.to_dict() for i in v]
                    output[cased_name] = v
                elif v._serialized_on_wire:
                    output[cased_name] = v.to_dict()
            elif meta.proto_type == "map":
                for k in v:
                    if hasattr(v[k], "to_dict"):
                        v[k] = v[k].to_dict()

                if v:
                    output[cased_name] = v
            elif v != self._get_field_default(field, meta):
                if meta.proto_type in INT_64_TYPES:
                    if isinstance(v, list):
                        output[cased_name] = [str(n) for n in v]
                    else:
                        output[cased_name] = str(v)
                elif meta.proto_type == TYPE_BYTES:
                    if isinstance(v, list):
                        output[cased_name] = [b64encode(b).decode("utf8") for b in v]
                    else:
                        output[cased_name] = b64encode(v).decode("utf8")
                elif meta.proto_type == TYPE_ENUM:
                    enum_values = list(self._cls_for(field)) # type: ignore
                    if isinstance(v, list):
                        output[cased_name] = [enum_values[e].name for e in v]
                    else:
                        output[cased_name] = enum_values[v].name
                else:
                    output[cased_name] = v
        return output

    def from_dict(self: T, value: dict) -> T:
        """
        Parse the key/value pairs in `value` into this message instance. This
        returns the instance itself and is therefore assignable and chainable.
        """
        self._serialized_on_wire = True
        fields_by_name = {f.name: f for f in dataclasses.fields(self)}
        for key in value:
            snake_cased = safe_snake_case(key)
            if snake_cased in fields_by_name:
                field = fields_by_name[snake_cased]
                meta = FieldMetadata.get(field)

                if value[key] is not None:
                    if meta.proto_type == "message":
                        v = getattr(self, field.name)
                        if isinstance(v, list):
                            cls = self._cls_for(field)
                            for i in range(len(value[key])):
                                v.append(cls().from_dict(value[key][i]))
                        elif isinstance(v, datetime):
                            v = datetime.fromisoformat(
                                value[key].replace("Z", "+00:00")
                            )
                            setattr(self, field.name, v)
                        elif isinstance(v, timedelta):
                            v = timedelta(seconds=float(value[key][:-1]))
                            setattr(self, field.name, v)
                        elif meta.wraps:
                            setattr(self, field.name, value[key])
                        else:
                            v.from_dict(value[key])
                    elif meta.map_types and meta.map_types[1] == TYPE_MESSAGE:
                        v = getattr(self, field.name)
                        cls = self._cls_for(field, index=1)
                        for k in value[key]:
                            v[k] = cls().from_dict(value[key][k])
                    else:
                        v = value[key]
                        if meta.proto_type in INT_64_TYPES:
                            if isinstance(value[key], list):
                                v = [int(n) for n in value[key]]
                            else:
                                v = int(value[key])
                        elif meta.proto_type == TYPE_BYTES:
                            if isinstance(value[key], list):
                                v = [b64decode(n) for n in value[key]]
                            else:
                                v = b64decode(value[key])
                        elif meta.proto_type == TYPE_ENUM:
                            enum_cls = self._cls_for(field)
                            if isinstance(v, list):
                                v = [enum_cls.from_string(e) for e in v]
                            elif isinstance(v, str):
                                v = enum_cls.from_string(v)

                        if v is not None:
                            setattr(self, field.name, v)
        return self

    def to_json(self, indent: Union[None, int, str] = None) -> str:
        """Returns the encoded JSON representation of this message instance."""
        return json.dumps(self.to_dict(), indent=indent)

    def from_json(self: T, value: Union[str, bytes]) -> T:
        """
        Parse the key/value pairs in `value` into this message instance. This
        returns the instance itself and is therefore assignable and chainable.
        """
        return self.from_dict(json.loads(value))


def serialized_on_wire(message: Message) -> bool:
    """
    True if this message was or should be serialized on the wire. This can
    be used to detect presence (e.g. optional wrapper message) and is used
    internally during parsing/serialization.
    """
    return message._serialized_on_wire


def which_one_of(message: Message, group_name: str) -> Tuple[str, Any]:
    """Return the name and value of a message's one-of field group."""
    field = message._group_map["groups"].get(group_name, {}).get("current")
    if not field:
        return ("", None)
    return (field.name, getattr(message, field.name))


@dataclasses.dataclass
class _Duration(Message):
    # Signed seconds of the span of time. Must be from -315,576,000,000 to
    # +315,576,000,000 inclusive. Note: these bounds are computed from: 60
    # sec/min * 60 min/hr * 24 hr/day * 365.25 days/year * 10000 years
    seconds: int = int64_field(1)
    # Signed fractions of a second at nanosecond resolution of the span of time.
    # Durations less than one second are represented with a 0 `seconds` field and
    # a positive or negative `nanos` field. For durations of one second or more,
    # a non-zero value for the `nanos` field must be of the same sign as the
    # `seconds` field. Must be from -999,999,999 to +999,999,999 inclusive.
    nanos: int = int32_field(2)

    def to_timedelta(self) -> timedelta:
        return timedelta(seconds=self.seconds, microseconds=self.nanos / 1e3)

    @staticmethod
    def delta_to_json(delta: timedelta) -> str:
        parts = str(delta.total_seconds()).split(".")
        if len(parts) > 1:
            while len(parts[1]) not in [3, 6, 9]:
                parts[1] = parts[1] + "0"
        return ".".join(parts) + "s"


@dataclasses.dataclass
class _Timestamp(Message):
    # Represents seconds of UTC time since Unix epoch 1970-01-01T00:00:00Z. Must
    # be from 0001-01-01T00:00:00Z to 9999-12-31T23:59:59Z inclusive.
    seconds: int = int64_field(1)
    # Non-negative fractions of a second at nanosecond resolution. Negative
    # second values with fractions must still have non-negative nanos values that
    # count forward in time. Must be from 0 to 999,999,999 inclusive.
    nanos: int = int32_field(2)

    def to_datetime(self) -> datetime:
        ts = self.seconds + (self.nanos / 1e9)
        return datetime.fromtimestamp(ts, tz=timezone.utc)

    @staticmethod
    def timestamp_to_json(dt: datetime) -> str:
        nanos = dt.microsecond * 1e3
        copy = dt.replace(microsecond=0, tzinfo=None)
        result = copy.isoformat()
        if (nanos % 1e9) == 0:
            # If there are 0 fractional digits, the fractional
            # point '.' should be omitted when serializing.
            return result + "Z"
        if (nanos % 1e6) == 0:
            # Serialize 3 fractional digits.
            return result + ".%03dZ" % (nanos / 1e6)
        if (nanos % 1e3) == 0:
            # Serialize 6 fractional digits.
            return result + ".%06dZ" % (nanos / 1e3)
        # Serialize 9 fractional digits.
        return result + ".%09dZ" % nanos


class _WrappedMessage(Message):
    """
    Google protobuf wrapper types base class. JSON representation is just the
    value itself.
    """
    value: Any

    def to_dict(self, casing: Casing = Casing.CAMEL) -> Any:
        return self.value

    def from_dict(self: T, value: Any) -> T:
        if value is not None:
            self.value = value
        return self


@dataclasses.dataclass
class _BoolValue(_WrappedMessage):
    value: bool = bool_field(1)


@dataclasses.dataclass
class _Int32Value(_WrappedMessage):
    value: int = int32_field(1)


@dataclasses.dataclass
class _UInt32Value(_WrappedMessage):
    value: int = uint32_field(1)


@dataclasses.dataclass
class _Int64Value(_WrappedMessage):
    value: int = int64_field(1)


@dataclasses.dataclass
class _UInt64Value(_WrappedMessage):
    value: int = uint64_field(1)


@dataclasses.dataclass
class _FloatValue(_WrappedMessage):
    value: float = float_field(1)


@dataclasses.dataclass
class _DoubleValue(_WrappedMessage):
    value: float = double_field(1)


@dataclasses.dataclass
class _StringValue(_WrappedMessage):
    value: str = string_field(1)


@dataclasses.dataclass
class _BytesValue(_WrappedMessage):
    value: bytes = bytes_field(1)


def _get_wrapper(proto_type: str) -> Type:
    """Get the wrapper message class for a wrapped type."""
    return {
        TYPE_BOOL: _BoolValue,
        TYPE_INT32: _Int32Value,
        TYPE_UINT32: _UInt32Value,
        TYPE_INT64: _Int64Value,
        TYPE_UINT64: _UInt64Value,
        TYPE_FLOAT: _FloatValue,
        TYPE_DOUBLE: _DoubleValue,
        TYPE_STRING: _StringValue,
        TYPE_BYTES: _BytesValue,
    }[proto_type]


class ServiceStub(ABC):
    """
    Base class for async gRPC service stubs.
    """

    def __init__(self, channel: grpclib.client.Channel) -> None:
        self.channel = channel

    async def _unary_unary(
        self, route: str, request_type: Type, response_type: Type[T], request: Any
    ) -> T:
        """Make a unary request and return the response."""
        async with self.channel.request(
            route, grpclib.const.Cardinality.UNARY_UNARY, request_type, response_type
        ) as stream:
            await stream.send_message(request, end=True)
            response = await stream.recv_message()
            assert response is not None
            return response

    async def _unary_stream(
        self, route: str, request_type: Type, response_type: Type[T], request: Any
    ) -> AsyncGenerator[T, None]:
        """Make a unary request and return the stream response iterator."""
        async with self.channel.request(
            route, grpclib.const.Cardinality.UNARY_STREAM, request_type, response_type
        ) as stream:
            await stream.send_message(request, end=True)
            async for message in stream:
                yield message
