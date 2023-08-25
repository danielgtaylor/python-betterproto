use super::{
    custom_message::CustomMessageBuilder, map_entry::MapEntryBuilder, DecodeResult, MessageBuilder,
};
use crate::{
    betterproto_interop::InteropResult,
    descriptors::ProtoType,
    well_known_types::{
        BoolValue, BytesValue, DoubleValue, Duration, FloatValue, Int32Value, Int64Value,
        StringValue, Timestamp, UInt32Value, UInt64Value,
    },
};
use prost::{
    bytes::Buf,
    encoding::{self as enc, DecodeContext, WireType},
    Message,
};
use pyo3::{
    types::{IntoPyDict, PyBytes},
    IntoPy, PyObject, Python, ToPyObject,
};

pub struct ValueBuilder<'a, 'py> {
    py: Python<'py>,
    proto_type: &'a ProtoType,
    value: Value,
}
enum Value {
    Unset,
    Single(PyObject),
    Repeated(Vec<PyObject>),
    Map(Vec<(PyObject, PyObject)>),
}

impl<'a, 'py> ValueBuilder<'a, 'py> {
    pub fn new(py: Python<'py>, proto_type: &'a ProtoType) -> Self {
        ValueBuilder {
            py,
            proto_type,
            value: Value::Unset,
        }
    }

    pub fn reset(&mut self) {
        self.value = Value::Unset;
    }

    pub fn into_object(self) -> Option<PyObject> {
        let py = self.py;
        match self.value {
            Value::Unset => None,
            Value::Single(obj) => Some(obj),
            Value::Repeated(ls) => Some(ls.to_object(py)),
            Value::Map(ls) => Some(ls.into_py_dict(py).to_object(py)),
        }
    }

    pub fn parse_next_single(
        &mut self,
        wire_type: WireType,
        buf: &mut impl Buf,
    ) -> DecodeResult<()> {
        self.set_single(parse_next_value(self.py, self.proto_type, wire_type, buf)?);
        Ok(())
    }

    pub fn parse_next_list_entry(
        &mut self,
        wire_type: WireType,
        buf: &mut impl Buf,
    ) -> DecodeResult<()> {
        if let WireType::LengthDelimited = wire_type {
            if let Some(obs) = try_parse_next_packed(self.py, self.proto_type, buf)? {
                self.append_repeated(obs);
                return Ok(());
            }
        }
        let obj = parse_next_value(self.py, self.proto_type, wire_type, buf)?;
        self.push_repeated(obj);
        Ok(())
    }

    pub fn parse_next_map_entry(
        &mut self,
        wire_type: WireType,
        key_type: &ProtoType,
        buf: &mut impl Buf,
    ) -> DecodeResult<()> {
        let mut builder = MapEntryBuilder::new(self.py, key_type, self.proto_type);
        builder.parse_next_length_delimited(wire_type, buf)?;
        self.push_map_entry(builder.into_tuple()?);
        Ok(())
    }

    fn set_single(&mut self, obj: PyObject) {
        match &mut self.value {
            Value::Single(x) => *x = obj,
            _ => self.value = Value::Single(obj),
        }
    }

    fn push_repeated(&mut self, obj: PyObject) {
        match &mut self.value {
            Value::Repeated(ls) => ls.push(obj),
            _ => self.value = Value::Repeated(vec![obj]),
        }
    }

    fn append_repeated(&mut self, mut objs: Vec<PyObject>) {
        match &mut self.value {
            Value::Repeated(ls) => ls.append(&mut objs),
            _ => self.value = Value::Repeated(objs),
        }
    }

    fn push_map_entry(&mut self, obj: (PyObject, PyObject)) {
        match &mut self.value {
            Value::Map(ls) => ls.push(obj),
            _ => self.value = Value::Map(vec![obj]),
        }
    }
}

fn parse_next_value(
    py: Python,
    proto_type: &ProtoType,
    wire_type: WireType,
    buf: &mut impl Buf,
) -> DecodeResult<PyObject> {
    let ctx = Default::default();
    match proto_type {
        ProtoType::Bool => {
            let mut value = Default::default();
            enc::bool::merge(wire_type, &mut value, buf, ctx)?;
            Ok(value.into_py(py))
        }
        ProtoType::Bytes => {
            let mut value = vec![];
            enc::bytes::merge(wire_type, &mut value, buf, ctx)?;
            Ok(PyBytes::new(py, &value).to_object(py))
        }
        ProtoType::Double => {
            let mut value = Default::default();
            enc::double::merge(wire_type, &mut value, buf, ctx)?;
            Ok(value.into_py(py))
        }
        ProtoType::Float => {
            let mut value = Default::default();
            enc::float::merge(wire_type, &mut value, buf, ctx)?;
            Ok(value.into_py(py))
        }
        ProtoType::Fixed32 => {
            let mut value = Default::default();
            enc::fixed32::merge(wire_type, &mut value, buf, ctx)?;
            Ok(value.into_py(py))
        }
        ProtoType::Fixed64 => {
            let mut value = Default::default();
            enc::fixed64::merge(wire_type, &mut value, buf, ctx)?;
            Ok(value.into_py(py))
        }
        ProtoType::Int32 => {
            let mut value = Default::default();
            enc::int32::merge(wire_type, &mut value, buf, ctx)?;
            Ok(value.into_py(py))
        }
        ProtoType::Int64 => {
            let mut value = Default::default();
            enc::int64::merge(wire_type, &mut value, buf, ctx)?;
            Ok(value.into_py(py))
        }
        ProtoType::Sfixed32 => {
            let mut value = Default::default();
            enc::sfixed32::merge(wire_type, &mut value, buf, ctx)?;
            Ok(value.into_py(py))
        }
        ProtoType::Sfixed64 => {
            let mut value = Default::default();
            enc::sfixed64::merge(wire_type, &mut value, buf, ctx)?;
            Ok(value.into_py(py))
        }
        ProtoType::Sint32 => {
            let mut value = Default::default();
            enc::sint32::merge(wire_type, &mut value, buf, ctx)?;
            Ok(value.into_py(py))
        }
        ProtoType::Sint64 => {
            let mut value = Default::default();
            enc::sint64::merge(wire_type, &mut value, buf, ctx)?;
            Ok(value.into_py(py))
        }
        ProtoType::String => {
            let mut value = Default::default();
            enc::string::merge(wire_type, &mut value, buf, ctx)?;
            Ok(value.into_py(py))
        }
        ProtoType::Uint32 => {
            let mut value = Default::default();
            enc::uint32::merge(wire_type, &mut value, buf, ctx)?;
            Ok(value.into_py(py))
        }
        ProtoType::Uint64 => {
            let mut value = Default::default();
            enc::uint64::merge(wire_type, &mut value, buf, ctx)?;
            Ok(value.into_py(py))
        }
        ProtoType::Enum(cls) => {
            let mut value = Default::default();
            enc::int32::merge(wire_type, &mut value, buf, ctx)?;
            Ok(cls.create_instance(py, value)?)
        }
        ProtoType::CustomMessage(cls) => {
            let mut builder = CustomMessageBuilder::new(py, cls.descriptor(py)?);
            builder.parse_next_length_delimited(wire_type, buf)?;
            let msg = cls.create_instance(py)?;
            builder.merge_into(msg)?;
            Ok(msg.to_object(py))
        }
        ProtoType::BoolValue => Ok(BoolValue::decode_length_delimited(buf)?.to_object(py)),
        ProtoType::BytesValue => Ok(BytesValue::decode_length_delimited(buf)?.to_object(py)),
        ProtoType::DoubleValue => Ok(DoubleValue::decode_length_delimited(buf)?.to_object(py)),
        ProtoType::FloatValue => Ok(FloatValue::decode_length_delimited(buf)?.to_object(py)),
        ProtoType::Int32Value => Ok(Int32Value::decode_length_delimited(buf)?.to_object(py)),
        ProtoType::Int64Value => Ok(Int64Value::decode_length_delimited(buf)?.to_object(py)),
        ProtoType::UInt32Value => Ok(UInt32Value::decode_length_delimited(buf)?.to_object(py)),
        ProtoType::UInt64Value => Ok(UInt64Value::decode_length_delimited(buf)?.to_object(py)),
        ProtoType::StringValue => Ok(StringValue::decode_length_delimited(buf)?.to_object(py)),
        ProtoType::Timestamp => Ok(Timestamp::decode_length_delimited(buf)?.to_object(py)),
        ProtoType::Duration => Ok(Duration::decode_length_delimited(buf)?.to_object(py)),
    }
}

fn try_parse_next_packed(
    py: Python,
    proto_type: &ProtoType,
    buf: &mut impl Buf,
) -> DecodeResult<Option<Vec<PyObject>>> {
    match proto_type {
        ProtoType::Bool => Some(parse_next_packed(py, enc::bool::merge_repeated, buf)),
        ProtoType::Double => Some(parse_next_packed(py, enc::double::merge_repeated, buf)),
        ProtoType::Float => Some(parse_next_packed(py, enc::float::merge_repeated, buf)),
        ProtoType::Fixed32 => Some(parse_next_packed(py, enc::fixed32::merge_repeated, buf)),
        ProtoType::Fixed64 => Some(parse_next_packed(py, enc::fixed64::merge_repeated, buf)),
        ProtoType::Sfixed32 => Some(parse_next_packed(py, enc::sfixed32::merge_repeated, buf)),
        ProtoType::Sfixed64 => Some(parse_next_packed(py, enc::sfixed64::merge_repeated, buf)),
        ProtoType::Int32 => Some(parse_next_packed(py, enc::int32::merge_repeated, buf)),
        ProtoType::Int64 => Some(parse_next_packed(py, enc::int64::merge_repeated, buf)),
        ProtoType::Uint32 => Some(parse_next_packed(py, enc::uint32::merge_repeated, buf)),
        ProtoType::Uint64 => Some(parse_next_packed(py, enc::uint64::merge_repeated, buf)),
        ProtoType::Sint32 => Some(parse_next_packed(py, enc::sint32::merge_repeated, buf)),
        ProtoType::Sint64 => Some(parse_next_packed(py, enc::sint64::merge_repeated, buf)),
        ProtoType::Enum(cls) => {
            let mut ls = vec![];
            enc::int32::merge_repeated(
                WireType::LengthDelimited,
                &mut ls,
                buf,
                Default::default(),
            )?;
            let res = ls
                .into_iter()
                .map(|x| cls.create_instance(py, x))
                .collect::<InteropResult<Vec<_>>>()?;
            Some(Ok(res))
        }
        _ => None,
    }
    .transpose()
}

fn parse_next_packed<B, R, T>(py: Python, merger: R, buf: &mut B) -> DecodeResult<Vec<PyObject>>
where
    B: Buf,
    R: FnOnce(WireType, &mut Vec<T>, &mut B, DecodeContext) -> Result<(), prost::DecodeError>,
    T: ToPyObject,
{
    let mut ls = vec![];
    merger(
        WireType::LengthDelimited,
        &mut ls,
        buf,
        DecodeContext::default(),
    )?;
    let res = ls.into_iter().map(|x| x.to_object(py)).collect::<Vec<_>>();
    Ok(res)
}
