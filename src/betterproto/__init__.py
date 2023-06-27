import dataclasses
import enum
import json
import math
import struct
import sys
import typing
import warnings
from abc import ABC
from base64 import (
    b64decode,
    b64encode,
)
from copy import deepcopy
from datetime import (
    datetime,
    timedelta,
    timezone,
)
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Generator,
    Iterable,
    List,
    Mapping,
    Optional,
    Set,
    Tuple,
    Type,
    Union,
    get_type_hints,
)

from dateutil.parser import isoparse

from ._types import T
from ._version import __version__
from .casing import (
    camel_case,
    safe_snake_case,
    snake_case,
)
from .grpc.grpclib_client import ServiceStub


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
def datetime_default_gen() -> datetime:
    return datetime(1970, 1, 1, tzinfo=timezone.utc)


DATETIME_ZERO = datetime_default_gen()


# Special protobuf json doubles
INFINITY = "Infinity"
NEG_INFINITY = "-Infinity"
NAN = "NaN"


class Casing(enum.Enum):
    """Casing constants for serialization."""

    CAMEL = camel_case  #: A camelCase sterilization function.
    SNAKE = snake_case  #: A snake_case sterilization function.


PLACEHOLDER: Any = object()


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
    # Is the field optional
    optional: Optional[bool] = False

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
    optional: bool = False,
) -> dataclasses.Field:
    """Creates a dataclass field with attached protobuf metadata."""
    return dataclasses.field(
        default=None if optional else PLACEHOLDER,
        metadata={
            "betterproto": FieldMetadata(
                number, proto_type, map_types, group, wraps, optional
            )
        },
    )


# Note: the fields below return `Any` to prevent type errors in the generated
# data classes since the types won't match with `Field` and they get swapped
# out at runtime. The generated dataclass variables are still typed correctly.


def enum_field(number: int, group: Optional[str] = None, optional: bool = False) -> Any:
    return dataclass_field(number, TYPE_ENUM, group=group, optional=optional)


def bool_field(number: int, group: Optional[str] = None, optional: bool = False) -> Any:
    return dataclass_field(number, TYPE_BOOL, group=group, optional=optional)


def int32_field(
    number: int, group: Optional[str] = None, optional: bool = False
) -> Any:
    return dataclass_field(number, TYPE_INT32, group=group, optional=optional)


def int64_field(
    number: int, group: Optional[str] = None, optional: bool = False
) -> Any:
    return dataclass_field(number, TYPE_INT64, group=group, optional=optional)


def uint32_field(
    number: int, group: Optional[str] = None, optional: bool = False
) -> Any:
    return dataclass_field(number, TYPE_UINT32, group=group, optional=optional)


def uint64_field(
    number: int, group: Optional[str] = None, optional: bool = False
) -> Any:
    return dataclass_field(number, TYPE_UINT64, group=group, optional=optional)


def sint32_field(
    number: int, group: Optional[str] = None, optional: bool = False
) -> Any:
    return dataclass_field(number, TYPE_SINT32, group=group, optional=optional)


def sint64_field(
    number: int, group: Optional[str] = None, optional: bool = False
) -> Any:
    return dataclass_field(number, TYPE_SINT64, group=group, optional=optional)


def float_field(
    number: int, group: Optional[str] = None, optional: bool = False
) -> Any:
    return dataclass_field(number, TYPE_FLOAT, group=group, optional=optional)


def double_field(
    number: int, group: Optional[str] = None, optional: bool = False
) -> Any:
    return dataclass_field(number, TYPE_DOUBLE, group=group, optional=optional)


def fixed32_field(
    number: int, group: Optional[str] = None, optional: bool = False
) -> Any:
    return dataclass_field(number, TYPE_FIXED32, group=group, optional=optional)


def fixed64_field(
    number: int, group: Optional[str] = None, optional: bool = False
) -> Any:
    return dataclass_field(number, TYPE_FIXED64, group=group, optional=optional)


def sfixed32_field(
    number: int, group: Optional[str] = None, optional: bool = False
) -> Any:
    return dataclass_field(number, TYPE_SFIXED32, group=group, optional=optional)


def sfixed64_field(
    number: int, group: Optional[str] = None, optional: bool = False
) -> Any:
    return dataclass_field(number, TYPE_SFIXED64, group=group, optional=optional)


def string_field(
    number: int, group: Optional[str] = None, optional: bool = False
) -> Any:
    return dataclass_field(number, TYPE_STRING, group=group, optional=optional)


def bytes_field(
    number: int, group: Optional[str] = None, optional: bool = False
) -> Any:
    return dataclass_field(number, TYPE_BYTES, group=group, optional=optional)


def message_field(
    number: int,
    group: Optional[str] = None,
    wraps: Optional[str] = None,
    optional: bool = False,
) -> Any:
    return dataclass_field(
        number, TYPE_MESSAGE, group=group, wraps=wraps, optional=optional
    )


def map_field(
    number: int, key_type: str, value_type: str, group: Optional[str] = None
) -> Any:
    return dataclass_field(
        number, TYPE_MAP, map_types=(key_type, value_type), group=group
    )


class Enum(enum.IntEnum):
    """
    The base class for protobuf enumerations, all generated enumerations will inherit
    from this. Bases :class:`enum.IntEnum`.
    """

    @classmethod
    def from_string(cls, name: str) -> "Enum":
        """Return the value which corresponds to the string name.

        Parameters
        -----------
        name: :class:`str`
            The name of the enum member to get

        Raises
        -------
        :exc:`ValueError`
            The member was not found in the Enum.
        """
        try:
            return cls._member_map_[name]  # type: ignore
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
            value = _Timestamp.from_datetime(value)
        elif isinstance(value, timedelta):
            # Convert the `timedelta` to a duration message.
            value = _Duration.from_timedelta(value)
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
    value: Any
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
    value: float
        Value to dump

    Returns
    -------
    Union[float, str]
        Dumped value, either a float or the strings
    """
    if value == float("inf"):
        return INFINITY
    if value == -float("inf"):
        return NEG_INFINITY
    if isinstance(value, float) and math.isnan(value):
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


class ProtoClassMetadata:
    __slots__ = (
        "oneof_group_by_field",
        "oneof_field_by_group",
        "default_gen",
        "cls_by_field",
        "field_name_by_number",
        "meta_by_field_name",
        "sorted_field_names",
    )

    oneof_group_by_field: Dict[str, str]
    oneof_field_by_group: Dict[str, Set[dataclasses.Field]]
    field_name_by_number: Dict[int, str]
    meta_by_field_name: Dict[str, FieldMetadata]
    sorted_field_names: Tuple[str, ...]
    default_gen: Dict[str, Callable[[], Any]]
    cls_by_field: Dict[str, Type]

    def __init__(self, cls: Type["Message"]):
        by_field = {}
        by_group: Dict[str, Set] = {}
        by_field_name = {}
        by_field_number = {}

        fields = dataclasses.fields(cls)
        for field in fields:
            meta = FieldMetadata.get(field)

            if meta.group:
                # This is part of a one-of group.
                by_field[field.name] = meta.group

                by_group.setdefault(meta.group, set()).add(field)

            by_field_name[field.name] = meta
            by_field_number[meta.number] = field.name

        self.oneof_group_by_field = by_field
        self.oneof_field_by_group = by_group
        self.field_name_by_number = by_field_number
        self.meta_by_field_name = by_field_name
        self.sorted_field_names = tuple(
            by_field_number[number] for number in sorted(by_field_number)
        )
        self.default_gen = self._get_default_gen(cls, fields)
        self.cls_by_field = self._get_cls_by_field(cls, fields)

    @staticmethod
    def _get_default_gen(
        cls: Type["Message"], fields: Iterable[dataclasses.Field]
    ) -> Dict[str, Callable[[], Any]]:
        return {field.name: cls._get_field_default_gen(field) for field in fields}

    @staticmethod
    def _get_cls_by_field(
        cls: Type["Message"], fields: Iterable[dataclasses.Field]
    ) -> Dict[str, Type]:
        field_cls = {}

        for field in fields:
            meta = FieldMetadata.get(field)
            if meta.proto_type == TYPE_MAP:
                assert meta.map_types
                kt = cls._cls_for(field, index=0)
                vt = cls._cls_for(field, index=1)
                field_cls[field.name] = dataclasses.make_dataclass(
                    "Entry",
                    [
                        ("key", kt, dataclass_field(1, meta.map_types[0])),
                        ("value", vt, dataclass_field(2, meta.map_types[1])),
                    ],
                    bases=(Message,),
                )
                field_cls[f"{field.name}.value"] = vt
            else:
                field_cls[field.name] = cls._cls_for(field)

        return field_cls


class Message(ABC):
    """
    The base class for protobuf messages, all generated messages will inherit from
    this. This class registers the message fields which are used by the serializers and
    parsers to go between the Python, binary and JSON representations of the message.

    .. container:: operations

        .. describe:: bytes(x)

            Calls :meth:`__bytes__`.

        .. describe:: bool(x)

            Calls :meth:`__bool__`.
    """

    _serialized_on_wire: bool
    _unknown_fields: bytes
    _group_current: Dict[str, str]

    def __post_init__(self) -> None:
        # Keep track of whether every field was default
        all_sentinel = True

        # Set current field of each group after `__init__` has already been run.
        group_current: Dict[str, Optional[str]] = {}
        for field_name, meta in self._betterproto.meta_by_field_name.items():
            if meta.group:
                group_current.setdefault(meta.group)

            value = self.__raw_get(field_name)
            if value != PLACEHOLDER and not (meta.optional and value is None):
                # Found a non-sentinel value
                all_sentinel = False

                if meta.group:
                    # This was set, so make it the selected value of the one-of.
                    group_current[meta.group] = field_name

        # Now that all the defaults are set, reset it!
        self.__dict__["_serialized_on_wire"] = not all_sentinel
        self.__dict__["_unknown_fields"] = b""
        self.__dict__["_group_current"] = group_current

    def __raw_get(self, name: str) -> Any:
        return super().__getattribute__(name)

    def __eq__(self, other) -> bool:
        if type(self) is not type(other):
            return False

        for field_name in self._betterproto.meta_by_field_name:
            self_val = self.__raw_get(field_name)
            other_val = other.__raw_get(field_name)
            if self_val is PLACEHOLDER:
                if other_val is PLACEHOLDER:
                    continue
                self_val = self._get_field_default(field_name)
            elif other_val is PLACEHOLDER:
                other_val = other._get_field_default(field_name)

            if self_val != other_val:
                # We consider two nan values to be the same for the
                # purposes of comparing messages (otherwise a message
                # is not equal to itself)
                if (
                    isinstance(self_val, float)
                    and isinstance(other_val, float)
                    and math.isnan(self_val)
                    and math.isnan(other_val)
                ):
                    continue
                else:
                    return False

        return True

    def __repr__(self) -> str:
        parts = [
            f"{field_name}={value!r}"
            for field_name in self._betterproto.sorted_field_names
            for value in (self.__raw_get(field_name),)
            if value is not PLACEHOLDER
        ]
        return f"{self.__class__.__name__}({', '.join(parts)})"

    if not TYPE_CHECKING:

        def __getattribute__(self, name: str) -> Any:
            """
            Lazily initialize default values to avoid infinite recursion for recursive
            message types
            """
            value = super().__getattribute__(name)
            if value is not PLACEHOLDER:
                return value

            value = self._get_field_default(name)
            super().__setattr__(name, value)
            return value

    def __setattr__(self, attr: str, value: Any) -> None:
        if (
            isinstance(value, Message)
            and hasattr(value, "_betterproto")
            and not value._betterproto.meta_by_field_name
        ):
            value._serialized_on_wire = True

        if attr != "_serialized_on_wire":
            # Track when a field has been set.
            self.__dict__["_serialized_on_wire"] = True

        if hasattr(self, "_group_current"):  # __post_init__ had already run
            if attr in self._betterproto.oneof_group_by_field:
                group = self._betterproto.oneof_group_by_field[attr]
                for field in self._betterproto.oneof_field_by_group[group]:
                    if field.name == attr:
                        self._group_current[group] = field.name
                    else:
                        super().__setattr__(field.name, PLACEHOLDER)

        super().__setattr__(attr, value)

    def __bool__(self) -> bool:
        """True if the Message has any fields with non-default values."""
        return any(
            self.__raw_get(field_name)
            not in (PLACEHOLDER, self._get_field_default(field_name))
            for field_name in self._betterproto.meta_by_field_name
        )

    def __deepcopy__(self: T, _: Any = {}) -> T:
        kwargs = {}
        for name in self._betterproto.sorted_field_names:
            value = self.__raw_get(name)
            if value is not PLACEHOLDER:
                kwargs[name] = deepcopy(value)
        return self.__class__(**kwargs)  # type: ignore

    @property
    def _betterproto(self) -> ProtoClassMetadata:
        """
        Lazy initialize metadata for each protobuf class.
        It may be initialized multiple times in a multi-threaded environment,
        but that won't affect the correctness.
        """
        meta = getattr(self.__class__, "_betterproto_meta", None)
        if not meta:
            meta = ProtoClassMetadata(self.__class__)
            self.__class__._betterproto_meta = meta  # type: ignore
        return meta

    def __bytes__(self) -> bytes:
        """
        Get the binary encoded Protobuf representation of this message instance.
        """
        output = bytearray()
        for field_name, meta in self._betterproto.meta_by_field_name.items():
            value = getattr(self, field_name)

            if value is None:
                # Optional items should be skipped. This is used for the Google
                # wrapper types and proto3 field presence/optional fields.
                continue

            # Being selected in a a group means this field is the one that is
            # currently set in a `oneof` group, so it must be serialized even
            # if the value is the default zero value.
            #
            # Note that proto3 field presence/optional fields are put in a
            # synthetic single-item oneof by protoc, which helps us ensure we
            # send the value even if the value is the default zero value.
            selected_in_group = (
                meta.group and self._group_current[meta.group] == field_name
            )

            # Empty messages can still be sent on the wire if they were
            # set (or received empty).
            serialize_empty = isinstance(value, Message) and value._serialized_on_wire

            include_default_value_for_oneof = self._include_default_value_for_oneof(
                field_name=field_name, meta=meta
            )

            if value == self._get_field_default(field_name) and not (
                selected_in_group or serialize_empty or include_default_value_for_oneof
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
                    buf = bytearray()
                    for item in value:
                        buf += _preprocess_single(meta.proto_type, "", item)
                    output += _serialize_single(meta.number, TYPE_BYTES, buf)
                else:
                    for item in value:
                        output += (
                            _serialize_single(
                                meta.number,
                                meta.proto_type,
                                item,
                                wraps=meta.wraps or "",
                                serialize_empty=True,
                            )
                            # if it's an empty message it still needs to be represented
                            # as an item in the repeated list
                            or b"\n\x00"
                        )

            elif isinstance(value, dict):
                for k, v in value.items():
                    assert meta.map_types
                    sk = _serialize_single(1, meta.map_types[0], k)
                    sv = _serialize_single(2, meta.map_types[1], v)
                    output += _serialize_single(meta.number, meta.proto_type, sk + sv)
            else:
                # If we have an empty string and we're including the default value for
                # a oneof, make sure we serialize it. This ensures that the byte string
                # output isn't simply an empty string. This also ensures that round trip
                # serialization will keep `which_one_of` calls consistent.
                if (
                    isinstance(value, str)
                    and value == ""
                    and include_default_value_for_oneof
                ):
                    serialize_empty = True

                output += _serialize_single(
                    meta.number,
                    meta.proto_type,
                    value,
                    serialize_empty=serialize_empty or bool(selected_in_group),
                    wraps=meta.wraps or "",
                )

        output += self._unknown_fields
        return bytes(output)

    # For compatibility with other libraries
    def SerializeToString(self: T) -> bytes:
        """
        Get the binary encoded Protobuf representation of this message instance.

        .. note::
            This is a method for compatibility with other libraries,
            you should really use ``bytes(x)``.

        Returns
        --------
        :class:`bytes`
            The binary encoded Protobuf representation of this message instance
        """
        return bytes(self)

    @classmethod
    def _type_hint(cls, field_name: str) -> Type:
        return cls._type_hints()[field_name]

    @classmethod
    def _type_hints(cls) -> Dict[str, Type]:
        module = sys.modules[cls.__module__]
        return get_type_hints(cls, module.__dict__, {})

    @classmethod
    def _cls_for(cls, field: dataclasses.Field, index: int = 0) -> Type:
        """Get the message class for a field from the type hints."""
        field_cls = cls._type_hint(field.name)
        if hasattr(field_cls, "__args__") and index >= 0:
            if field_cls.__args__ is not None:
                field_cls = field_cls.__args__[index]
        return field_cls

    def _get_field_default(self, field_name: str) -> Any:
        with warnings.catch_warnings():
            # ignore warnings when initialising deprecated field defaults
            warnings.filterwarnings("ignore", category=DeprecationWarning)
            return self._betterproto.default_gen[field_name]()

    @classmethod
    def _get_field_default_gen(cls, field: dataclasses.Field) -> Any:
        t = cls._type_hint(field.name)

        if hasattr(t, "__origin__"):
            if t.__origin__ is dict:
                # This is some kind of map (dict in Python).
                return dict
            elif t.__origin__ is list:
                # This is some kind of list (repeated) field.
                return list
            elif t.__origin__ is Union and t.__args__[1] is type(None):
                # This is an optional field (either wrapped, or using proto3
                # field presence). For setting the default we really don't care
                # what kind of field it is.
                return type(None)
            else:
                return t
        elif issubclass(t, Enum):
            # Enums always default to zero.
            return int
        elif t is datetime:
            # Offsets are relative to 1970-01-01T00:00:00Z
            return datetime_default_gen
        else:
            # This is either a primitive scalar or another message type. Calling
            # it should result in its zero value.
            return t

    def _postprocess_single(
        self, wire_type: int, meta: FieldMetadata, field_name: str, value: Any
    ) -> Any:
        """Adjusts values after parsing."""
        if wire_type == WIRE_VARINT:
            if meta.proto_type in (TYPE_INT32, TYPE_INT64):
                bits = int(meta.proto_type[3:])
                value = value & ((1 << bits) - 1)
                signbit = 1 << (bits - 1)
                value = int((value ^ signbit) - signbit)
            elif meta.proto_type in (TYPE_SINT32, TYPE_SINT64):
                # Undo zig-zag encoding
                value = (value >> 1) ^ (-(value & 1))
            elif meta.proto_type == TYPE_BOOL:
                # Booleans use a varint encoding, so convert it to true/false.
                value = value > 0
        elif wire_type in (WIRE_FIXED_32, WIRE_FIXED_64):
            fmt = _pack_fmt(meta.proto_type)
            value = struct.unpack(fmt, value)[0]
        elif wire_type == WIRE_LEN_DELIM:
            if meta.proto_type == TYPE_STRING:
                value = str(value, "utf-8")
            elif meta.proto_type == TYPE_MESSAGE:
                cls = self._betterproto.cls_by_field[field_name]

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
                value = self._betterproto.cls_by_field[field_name]().parse(value)

        return value

    def _include_default_value_for_oneof(
        self, field_name: str, meta: FieldMetadata
    ) -> bool:
        return (
            meta.group is not None and self._group_current.get(meta.group) == field_name
        )

    def parse(self: T, data: bytes) -> T:
        """
        Parse the binary encoded Protobuf into this message instance. This
        returns the instance itself and is therefore assignable and chainable.

        Parameters
        -----------
        data: :class:`bytes`
            The data to parse the protobuf from.

        Returns
        --------
        :class:`Message`
            The initialized message.
        """
        # Got some data over the wire
        self._serialized_on_wire = True
        proto_meta = self._betterproto
        for parsed in parse_fields(data):
            field_name = proto_meta.field_name_by_number.get(parsed.number)
            if not field_name:
                self._unknown_fields += parsed.raw
                continue

            meta = proto_meta.meta_by_field_name[field_name]

            value: Any
            if parsed.wire_type == WIRE_LEN_DELIM and meta.proto_type in PACKED_TYPES:
                # This is a packed repeated field.
                pos = 0
                value = []
                while pos < len(parsed.value):
                    if meta.proto_type in (TYPE_FLOAT, TYPE_FIXED32, TYPE_SFIXED32):
                        decoded, pos = parsed.value[pos : pos + 4], pos + 4
                        wire_type = WIRE_FIXED_32
                    elif meta.proto_type in (TYPE_DOUBLE, TYPE_FIXED64, TYPE_SFIXED64):
                        decoded, pos = parsed.value[pos : pos + 8], pos + 8
                        wire_type = WIRE_FIXED_64
                    else:
                        decoded, pos = decode_varint(parsed.value, pos)
                        wire_type = WIRE_VARINT
                    decoded = self._postprocess_single(
                        wire_type, meta, field_name, decoded
                    )
                    value.append(decoded)
            else:
                value = self._postprocess_single(
                    parsed.wire_type, meta, field_name, parsed.value
                )

            current = getattr(self, field_name)
            if meta.proto_type == TYPE_MAP:
                # Value represents a single key/value pair entry in the map.
                current[value.key] = value.value
            elif isinstance(current, list) and not isinstance(value, list):
                current.append(value)
            else:
                setattr(self, field_name, value)

        return self

    # For compatibility with other libraries.
    @classmethod
    def FromString(cls: Type[T], data: bytes) -> T:
        """
        Parse the binary encoded Protobuf into this message instance. This
        returns the instance itself and is therefore assignable and chainable.

        .. note::
            This is a method for compatibility with other libraries,
            you should really use :meth:`parse`.


        Parameters
        -----------
        data: :class:`bytes`
            The data to parse the protobuf from.

        Returns
        --------
        :class:`Message`
            The initialized message.
        """
        return cls().parse(data)

    def to_dict(
        self, casing: Casing = Casing.CAMEL, include_default_values: bool = False
    ) -> Dict[str, Any]:
        """
        Returns a JSON serializable dict representation of this object.

        Parameters
        -----------
        casing: :class:`Casing`
            The casing to use for key values. Default is :attr:`Casing.CAMEL` for
            compatibility purposes.
        include_default_values: :class:`bool`
            If ``True`` will include the default values of fields. Default is ``False``.
            E.g. an ``int32`` field will be included with a value of ``0`` if this is
            set to ``True``, otherwise this would be ignored.

        Returns
        --------
        Dict[:class:`str`, Any]
            The JSON serializable dict representation of this object.
        """
        output: Dict[str, Any] = {}
        field_types = self._type_hints()
        defaults = self._betterproto.default_gen
        for field_name, meta in self._betterproto.meta_by_field_name.items():
            field_is_repeated = defaults[field_name] is list
            value = getattr(self, field_name)
            cased_name = casing(field_name).rstrip("_")  # type: ignore
            if meta.proto_type == TYPE_MESSAGE:
                if isinstance(value, datetime):
                    if (
                        value != DATETIME_ZERO
                        or include_default_values
                        or self._include_default_value_for_oneof(
                            field_name=field_name, meta=meta
                        )
                    ):
                        output[cased_name] = _Timestamp.timestamp_to_json(value)
                elif isinstance(value, timedelta):
                    if (
                        value != timedelta(0)
                        or include_default_values
                        or self._include_default_value_for_oneof(
                            field_name=field_name, meta=meta
                        )
                    ):
                        output[cased_name] = _Duration.delta_to_json(value)
                elif meta.wraps:
                    if value is not None or include_default_values:
                        output[cased_name] = value
                elif field_is_repeated:
                    # Convert each item.
                    cls = self._betterproto.cls_by_field[field_name]
                    if cls == datetime:
                        value = [_Timestamp.timestamp_to_json(i) for i in value]
                    elif cls == timedelta:
                        value = [_Duration.delta_to_json(i) for i in value]
                    else:
                        value = [
                            i.to_dict(casing, include_default_values) for i in value
                        ]
                    if value or include_default_values:
                        output[cased_name] = value
                elif value is None:
                    if include_default_values:
                        output[cased_name] = value
                elif (
                    value._serialized_on_wire
                    or include_default_values
                    or self._include_default_value_for_oneof(
                        field_name=field_name, meta=meta
                    )
                ):
                    output[cased_name] = value.to_dict(casing, include_default_values)
            elif meta.proto_type == TYPE_MAP:
                output_map = {**value}
                for k in value:
                    if hasattr(value[k], "to_dict"):
                        output_map[k] = value[k].to_dict(casing, include_default_values)

                if value or include_default_values:
                    output[cased_name] = output_map
            elif (
                value != self._get_field_default(field_name)
                or include_default_values
                or self._include_default_value_for_oneof(
                    field_name=field_name, meta=meta
                )
            ):
                if meta.proto_type in INT_64_TYPES:
                    if field_is_repeated:
                        output[cased_name] = [str(n) for n in value]
                    elif value is None:
                        if include_default_values:
                            output[cased_name] = value
                    else:
                        output[cased_name] = str(value)
                elif meta.proto_type == TYPE_BYTES:
                    if field_is_repeated:
                        output[cased_name] = [
                            b64encode(b).decode("utf8") for b in value
                        ]
                    elif value is None and include_default_values:
                        output[cased_name] = value
                    else:
                        output[cased_name] = b64encode(value).decode("utf8")
                elif meta.proto_type == TYPE_ENUM:
                    if field_is_repeated:
                        enum_class = field_types[field_name].__args__[0]
                        if isinstance(value, typing.Iterable) and not isinstance(
                            value, str
                        ):
                            output[cased_name] = [enum_class(el).name for el in value]
                        else:
                            # transparently upgrade single value to repeated
                            output[cased_name] = [enum_class(value).name]
                    elif value is None:
                        if include_default_values:
                            output[cased_name] = value
                    elif meta.optional:
                        enum_class = field_types[field_name].__args__[0]
                        output[cased_name] = enum_class(value).name
                    else:
                        enum_class = field_types[field_name]  # noqa
                        output[cased_name] = enum_class(value).name
                elif meta.proto_type in (TYPE_FLOAT, TYPE_DOUBLE):
                    if field_is_repeated:
                        output[cased_name] = [_dump_float(n) for n in value]
                    else:
                        output[cased_name] = _dump_float(value)
                else:
                    output[cased_name] = value
        return output

    def from_dict(self: T, value: Mapping[str, Any]) -> T:
        """
        Parse the key/value pairs into the current message instance. This returns the
        instance itself and is therefore assignable and chainable.

        Parameters
        -----------
        value: Dict[:class:`str`, Any]
            The dictionary to parse from.

        Returns
        --------
        :class:`Message`
            The initialized message.
        """
        self._serialized_on_wire = True
        for key in value:
            field_name = safe_snake_case(key)
            meta = self._betterproto.meta_by_field_name.get(field_name)
            if not meta:
                continue

            if value[key] is not None:
                if meta.proto_type == TYPE_MESSAGE:
                    v = getattr(self, field_name)
                    cls = self._betterproto.cls_by_field[field_name]
                    if isinstance(v, list):
                        if cls == datetime:
                            v = [isoparse(item) for item in value[key]]
                        elif cls == timedelta:
                            v = [
                                timedelta(seconds=float(item[:-1]))
                                for item in value[key]
                            ]
                        else:
                            v = [cls().from_dict(item) for item in value[key]]
                    elif cls == datetime:
                        v = isoparse(value[key])
                        setattr(self, field_name, v)
                    elif cls == timedelta:
                        v = timedelta(seconds=float(value[key][:-1]))
                        setattr(self, field_name, v)
                    elif meta.wraps:
                        setattr(self, field_name, value[key])
                    elif v is None:
                        setattr(self, field_name, cls().from_dict(value[key]))
                    else:
                        # NOTE: `from_dict` mutates the underlying message, so no
                        # assignment here is necessary.
                        v.from_dict(value[key])
                elif meta.map_types and meta.map_types[1] == TYPE_MESSAGE:
                    v = getattr(self, field_name)
                    cls = self._betterproto.cls_by_field[f"{field_name}.value"]
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
                        enum_cls = self._betterproto.cls_by_field[field_name]
                        if isinstance(v, list):
                            v = [enum_cls.from_string(e) for e in v]
                        elif isinstance(v, str):
                            v = enum_cls.from_string(v)
                    elif meta.proto_type in (TYPE_FLOAT, TYPE_DOUBLE):
                        if isinstance(value[key], list):
                            v = [_parse_float(n) for n in value[key]]
                        else:
                            v = _parse_float(value[key])

                if v is not None:
                    setattr(self, field_name, v)
        return self

    def to_json(
        self,
        indent: Union[None, int, str] = None,
        include_default_values: bool = False,
        casing: Casing = Casing.CAMEL,
    ) -> str:
        """A helper function to parse the message instance into its JSON
        representation.

        This is equivalent to::

            json.dumps(message.to_dict(), indent=indent)

        Parameters
        -----------
        indent: Optional[Union[:class:`int`, :class:`str`]]
            The indent to pass to :func:`json.dumps`.

        include_default_values: :class:`bool`
            If ``True`` will include the default values of fields. Default is ``False``.
            E.g. an ``int32`` field will be included with a value of ``0`` if this is
            set to ``True``, otherwise this would be ignored.

        casing: :class:`Casing`
            The casing to use for key values. Default is :attr:`Casing.CAMEL` for
            compatibility purposes.

        Returns
        --------
        :class:`str`
            The JSON representation of the message.
        """
        return json.dumps(
            self.to_dict(include_default_values=include_default_values, casing=casing),
            indent=indent,
        )

    def from_json(self: T, value: Union[str, bytes]) -> T:
        """A helper function to return the message instance from its JSON
        representation. This returns the instance itself and is therefore assignable
        and chainable.

        This is equivalent to::

            return message.from_dict(json.loads(value))

        Parameters
        -----------
        value: Union[:class:`str`, :class:`bytes`]
            The value to pass to :func:`json.loads`.

        Returns
        --------
        :class:`Message`
            The initialized message.
        """
        return self.from_dict(json.loads(value))

    def to_pydict(
        self, casing: Casing = Casing.CAMEL, include_default_values: bool = False
    ) -> Dict[str, Any]:
        """
        Returns a python dict representation of this object.

        Parameters
        -----------
        casing: :class:`Casing`
            The casing to use for key values. Default is :attr:`Casing.CAMEL` for
            compatibility purposes.
        include_default_values: :class:`bool`
            If ``True`` will include the default values of fields. Default is ``False``.
            E.g. an ``int32`` field will be included with a value of ``0`` if this is
            set to ``True``, otherwise this would be ignored.

        Returns
        --------
        Dict[:class:`str`, Any]
            The python dict representation of this object.
        """
        output: Dict[str, Any] = {}
        defaults = self._betterproto.default_gen
        for field_name, meta in self._betterproto.meta_by_field_name.items():
            field_is_repeated = defaults[field_name] is list
            value = getattr(self, field_name)
            cased_name = casing(field_name).rstrip("_")  # type: ignore
            if meta.proto_type == TYPE_MESSAGE:
                if isinstance(value, datetime):
                    if (
                        value != DATETIME_ZERO
                        or include_default_values
                        or self._include_default_value_for_oneof(
                            field_name=field_name, meta=meta
                        )
                    ):
                        output[cased_name] = value
                elif isinstance(value, timedelta):
                    if (
                        value != timedelta(0)
                        or include_default_values
                        or self._include_default_value_for_oneof(
                            field_name=field_name, meta=meta
                        )
                    ):
                        output[cased_name] = value
                elif meta.wraps:
                    if value is not None or include_default_values:
                        output[cased_name] = value
                elif field_is_repeated:
                    # Convert each item.
                    value = [i.to_pydict(casing, include_default_values) for i in value]
                    if value or include_default_values:
                        output[cased_name] = value
                elif value is None:
                    if include_default_values:
                        output[cased_name] = None
                elif (
                    value._serialized_on_wire
                    or include_default_values
                    or self._include_default_value_for_oneof(
                        field_name=field_name, meta=meta
                    )
                ):
                    output[cased_name] = value.to_pydict(casing, include_default_values)
            elif meta.proto_type == TYPE_MAP:
                for k in value:
                    if hasattr(value[k], "to_pydict"):
                        value[k] = value[k].to_pydict(casing, include_default_values)

                if value or include_default_values:
                    output[cased_name] = value
            elif (
                value != self._get_field_default(field_name)
                or include_default_values
                or self._include_default_value_for_oneof(
                    field_name=field_name, meta=meta
                )
            ):
                output[cased_name] = value
        return output

    def from_pydict(self: T, value: Mapping[str, Any]) -> T:
        """
        Parse the key/value pairs into the current message instance. This returns the
        instance itself and is therefore assignable and chainable.

        Parameters
        -----------
        value: Dict[:class:`str`, Any]
            The dictionary to parse from.

        Returns
        --------
        :class:`Message`
            The initialized message.
        """
        self._serialized_on_wire = True
        for key in value:
            field_name = safe_snake_case(key)
            meta = self._betterproto.meta_by_field_name.get(field_name)
            if not meta:
                continue

            if value[key] is not None:
                if meta.proto_type == TYPE_MESSAGE:
                    v = getattr(self, field_name)
                    if isinstance(v, list):
                        cls = self._betterproto.cls_by_field[field_name]
                        for item in value[key]:
                            v.append(cls().from_pydict(item))
                    elif isinstance(v, datetime):
                        v = value[key]
                    elif isinstance(v, timedelta):
                        v = value[key]
                    elif meta.wraps:
                        v = value[key]
                    else:
                        # NOTE: `from_pydict` mutates the underlying message, so no
                        # assignment here is necessary.
                        v.from_pydict(value[key])
                elif meta.map_types and meta.map_types[1] == TYPE_MESSAGE:
                    v = getattr(self, field_name)
                    cls = self._betterproto.cls_by_field[f"{field_name}.value"]
                    for k in value[key]:
                        v[k] = cls().from_pydict(value[key][k])
                else:
                    v = value[key]

                if v is not None:
                    setattr(self, field_name, v)
        return self

    def is_set(self, name: str) -> bool:
        """
        Check if field with the given name has been set.

        Parameters
        -----------
        name: :class:`str`
            The name of the field to check for.

        Returns
        --------
        :class:`bool`
            `True` if field has been set, otherwise `False`.
        """
        default = (
            PLACEHOLDER
            if not self._betterproto.meta_by_field_name[name].optional
            else None
        )
        return self.__raw_get(name) is not default

    @classmethod
    def _validate_field_groups(cls, values):
        group_to_one_ofs = cls._betterproto_meta.oneof_field_by_group  # type: ignore
        field_name_to_meta = cls._betterproto_meta.meta_by_field_name  # type: ignore

        for group, field_set in group_to_one_ofs.items():

            if len(field_set) == 1:
                (field,) = field_set
                field_name = field.name
                meta = field_name_to_meta[field_name]

                # This is a synthetic oneof; we should ignore it's presence and not consider it as a oneof.
                if meta.optional:
                    continue

            set_fields = [
                field.name for field in field_set if values[field.name] is not None
            ]

            if not set_fields:
                raise ValueError(f"Group {group} has no value; all fields are None")
            elif len(set_fields) > 1:
                set_fields_str = ", ".join(set_fields)
                raise ValueError(
                    f"Group {group} has more than one value; fields {set_fields_str} are not None"
                )

        return values


def serialized_on_wire(message: Message) -> bool:
    """
    If this message was or should be serialized on the wire. This can be used to detect
    presence (e.g. optional wrapper message) and is used internally during
    parsing/serialization.

    Returns
    --------
    :class:`bool`
        Whether this message was or should be serialized on the wire.
    """
    return message._serialized_on_wire


def which_one_of(message: Message, group_name: str) -> Tuple[str, Optional[Any]]:
    """
    Return the name and value of a message's one-of field group.

    Returns
    --------
    Tuple[:class:`str`, Any]
        The field name and the value for that field.
    """
    field_name = message._group_current.get(group_name)
    if not field_name:
        return "", None
    return field_name, getattr(message, field_name)


# Circular import workaround: google.protobuf depends on base classes defined above.
from .lib.google.protobuf import (  # noqa
    BoolValue,
    BytesValue,
    DoubleValue,
    Duration,
    EnumValue,
    FloatValue,
    Int32Value,
    Int64Value,
    StringValue,
    Timestamp,
    UInt32Value,
    UInt64Value,
)


class _Duration(Duration):
    @classmethod
    def from_timedelta(
        cls, delta: timedelta, *, _1_microsecond: timedelta = timedelta(microseconds=1)
    ) -> "_Duration":
        total_ms = delta // _1_microsecond
        seconds = int(total_ms / 1e6)
        nanos = int((total_ms % 1e6) * 1e3)
        return cls(seconds, nanos)

    def to_timedelta(self) -> timedelta:
        return timedelta(seconds=self.seconds, microseconds=self.nanos / 1e3)

    @staticmethod
    def delta_to_json(delta: timedelta) -> str:
        parts = str(delta.total_seconds()).split(".")
        if len(parts) > 1:
            while len(parts[1]) not in (3, 6, 9):
                parts[1] = f"{parts[1]}0"
        return f"{'.'.join(parts)}s"


class _Timestamp(Timestamp):
    @classmethod
    def from_datetime(cls, dt: datetime) -> "_Timestamp":
        seconds = int(dt.timestamp())
        nanos = int(dt.microsecond * 1e3)
        return cls(seconds, nanos)

    def to_datetime(self) -> datetime:
        ts = self.seconds + (self.nanos / 1e9)
        return datetime.fromtimestamp(ts, tz=timezone.utc)

    @staticmethod
    def timestamp_to_json(dt: datetime) -> str:
        nanos = dt.microsecond * 1e3
        if dt.tzinfo is not None:
            # change timezone aware datetime objects to utc
            dt = dt.astimezone(timezone.utc)
        copy = dt.replace(microsecond=0, tzinfo=None)
        result = copy.isoformat()
        if (nanos % 1e9) == 0:
            # If there are 0 fractional digits, the fractional
            # point '.' should be omitted when serializing.
            return f"{result}Z"
        if (nanos % 1e6) == 0:
            # Serialize 3 fractional digits.
            return f"{result}.{int(nanos // 1e6) :03d}Z"
        if (nanos % 1e3) == 0:
            # Serialize 6 fractional digits.
            return f"{result}.{int(nanos // 1e3) :06d}Z"
        # Serialize 9 fractional digits.
        return f"{result}.{nanos:09d}"


def _get_wrapper(proto_type: str) -> Type:
    """Get the wrapper message class for a wrapped type."""

    # TODO: include ListValue and NullValue?
    return {
        TYPE_BOOL: BoolValue,
        TYPE_BYTES: BytesValue,
        TYPE_DOUBLE: DoubleValue,
        TYPE_FLOAT: FloatValue,
        TYPE_ENUM: EnumValue,
        TYPE_INT32: Int32Value,
        TYPE_INT64: Int64Value,
        TYPE_STRING: StringValue,
        TYPE_UINT32: UInt32Value,
        TYPE_UINT64: UInt64Value,
    }[proto_type]
