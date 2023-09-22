use pyo3::{
    types::{PyBytes, PyString},
    PyObject, Python, ToPyObject,
};

use crate::{
    betterproto_interop::{BetterprotoEnumClass, BetterprotoMessageClass, InteropResult},
    well_known_types::{Duration, Timestamp},
    Str,
};

#[derive(Debug)]
pub struct MessageDescriptor {
    pub fields: Vec<(u32, FieldDescriptor)>,
}

#[derive(Debug)]
pub struct FieldDescriptor {
    pub name: Str,
    pub attribute: FieldAttribute,
    pub value_type: ProtoType,
}

#[derive(Debug)]
pub enum FieldAttribute {
    None,
    Optional,
    Group(Str),
    Map(ProtoType),
    Repeated,
}

#[derive(Debug)]
pub enum ProtoType {
    Bool,
    Bytes,
    Int32,
    Int64,
    Uint32,
    Uint64,
    Float,
    Double,
    String,
    Enum(BetterprotoEnumClass),
    CustomMessage(BetterprotoMessageClass),
    Sint32,
    Sint64,
    Fixed32,
    Sfixed32,
    Fixed64,
    Sfixed64,
    BoolValue,
    BytesValue,
    DoubleValue,
    FloatValue,
    Int32Value,
    Int64Value,
    UInt32Value,
    UInt64Value,
    StringValue,
    Duration,
    Timestamp,
}

impl ProtoType {
    pub fn default_value(&self, py: Python) -> InteropResult<PyObject> {
        match self {
            Self::Bool => Ok(false.to_object(py)),
            Self::Bytes => Ok(PyBytes::new(py, &[]).to_object(py)),
            Self::Double | Self::Float => Ok(0_f64.to_object(py)),
            Self::Int32
            | Self::Int64
            | Self::Sint32
            | Self::Sint64
            | Self::Uint32
            | Self::Uint64
            | Self::Fixed32
            | Self::Fixed64
            | Self::Sfixed32
            | Self::Sfixed64 => Ok(0_i64.to_object(py)),
            Self::String => Ok(PyString::new(py, "").to_object(py)),
            Self::Enum(cls) => cls.create_instance(py, 0),
            Self::CustomMessage(cls) => Ok(cls.create_instance(py)?.to_object(py)),
            Self::BoolValue
            | Self::BytesValue
            | Self::FloatValue
            | Self::DoubleValue
            | Self::Int32Value
            | Self::Int64Value
            | Self::StringValue
            | Self::UInt32Value
            | Self::UInt64Value => Ok(py.None()),
            Self::Timestamp => Ok(Timestamp::default().to_object(py)),
            Self::Duration => Ok(Duration::default().to_object(py)),
        }
    }
}
