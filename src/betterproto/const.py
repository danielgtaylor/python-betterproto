# Proto 3 data types
from datetime import datetime, timezone


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
