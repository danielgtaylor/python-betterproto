use crate::{
    betterproto_interop::{BetterprotoEnumClass, BetterprotoMessageClass},
    Str,
};

#[derive(Debug)]
pub struct MessageDescriptor {
    pub fields: Vec<(u32, FieldDescriptor)>,
}

#[derive(Debug)]
pub struct FieldDescriptor {
    pub name: Str,
    pub cardinality: Cardinality,
    pub group: Option<Str>,
    pub value_type: ProtoType,
}

#[derive(Debug)]
pub enum Cardinality {
    Single,
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
