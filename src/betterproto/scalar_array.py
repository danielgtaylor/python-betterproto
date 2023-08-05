from typing import TypeVar, Any
from collections.abc import Sequence
from . import TYPE_DOUBLE, TYPE_FLOAT, TYPE_SFIXED32, TYPE_FIXED32, TYPE_FIXED64, TYPE_SFIXED64, _pack_fmt
import struct

NP_DOUBLE = 'float64'
NP_FLOAT = 'float32'
NP_SFIXED32 = 'int32'
NP_FIXED32 = 'uint32'
NP_SFIXED64 = 'int64'
NP_FIXED64 = 'uint64'

def _convert_types_np2proto(np_type: str) -> str:
    return {
        NP_DOUBLE: TYPE_DOUBLE,
        NP_FLOAT: TYPE_FLOAT,
        NP_SFIXED32: TYPE_SFIXED32,
        NP_FIXED32: TYPE_FIXED32,
        NP_SFIXED64: TYPE_SFIXED64,
        NP_FIXED64: TYPE_FIXED64
    }[np_type]

def _convert_types_proto2np(proto_type: str) -> str:
    return {
        TYPE_DOUBLE: NP_DOUBLE,
        TYPE_FLOAT: NP_FLOAT,
        TYPE_SFIXED32: NP_SFIXED32,
        TYPE_FIXED32: NP_FIXED32,
        TYPE_SFIXED64: NP_SFIXED64,
        TYPE_FIXED64: NP_FIXED64
    }[proto_type]

def _item_size(proto_type: str) -> int:
    return {
        TYPE_DOUBLE: 8,
        TYPE_FLOAT: 4,
        TYPE_SFIXED32: 4,
        TYPE_FIXED32: 4,
        TYPE_SFIXED64: 8,
        TYPE_FIXED64: 8
    }[proto_type]


T = TypeVar('T', covariant=True)

class ScalarArray(Sequence[T]):
    __data: bytes
    __item_size: int
    __proto_type: str

    def __init__(self, data: bytes, proto_type: str) -> None:
        self.__data = data
        self.__item_size = _item_size(proto_type)
        self.__proto_type = proto_type

    def __len__(self) -> int:
        return len(self.__data) // self.__item_size
    
    def __getitem__(self, i: int) -> T:
        if i < 0:
            i += len(self)
        if i < 0 or i >= len(self):
            raise IndexError

        value = self.__data[i*self.__item_size:(i+1)*self.__item_size]
        value = struct.unpack(_pack_fmt(self.__proto_type), value)[0]
        return value
    
    def __bytes__(self) -> bytes:
        return self.__data
    
    def __repr__(self) -> str:
        return str(list(self))

    def __array__(self):
        import numpy as np
        return np.frombuffer(self.__data, dtype=_convert_types_proto2np(self.__proto_type))

    def __json__(self):
        return list(self)
    
    def __eq__(self, other):
        if isinstance(other, ScalarArray):
            return self.__data == other.__data and self.__item_size == other.__item_size and self.__proto_type == other.__proto_type
        return isinstance(other, Sequence) and list(self) == list(other)
    
    @staticmethod
    def from_numpy(ar) -> 'ScalarArray[Any]':
        return ScalarArray(bytes(ar), _convert_types_np2proto(str(ar.dtype)))
