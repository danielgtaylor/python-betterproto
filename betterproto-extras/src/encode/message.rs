use super::{chunk::Chunk, EncodeResult};
use crate::{
    betterproto_interop::BetterprotoMessage,
    descriptors::{FieldAttribute, FieldDescriptor, MessageDescriptor, ProtoType},
    well_known_types::{
        BoolValue, BytesValue, DoubleValue, Duration, FloatValue, Int32Value, Int64Value,
        StringValue, Timestamp, UInt32Value, UInt64Value,
    },
};
use prost::{encoding as enc, Message};
use pyo3::{
    intern,
    types::{PyDict, PyList},
    PyAny, PyResult,
};

pub struct MessageEncoder(Vec<Chunk>);

impl MessageEncoder {
    pub fn from_betterproto_msg(
        msg: BetterprotoMessage,
        descriptor: &MessageDescriptor,
    ) -> EncodeResult<Self> {
        let mut encoder = MessageEncoder::new();
        for (tag, field) in descriptor.fields.iter() {
            if let Some(value) = msg.get_field(&field.name)? {
                encoder.load_field(*tag, field, value)?;
            }
        }
        encoder.load_unknown_fields(msg.get_unknown_fields()?);
        Ok(encoder)
    }

    pub fn into_vec(self) -> Vec<u8> {
        let capacity = self.encoded_len();
        let mut buf = Vec::with_capacity(capacity);
        self.encode(&mut buf);
        debug_assert_eq!(capacity, buf.len());
        buf
    }

    fn new() -> Self {
        Self(vec![])
    }

    pub(super) fn encoded_len(&self) -> usize {
        self.0
            .iter()
            .map(|chunk| chunk.encoded_len())
            .sum::<usize>()
    }

    pub(super) fn encode(&self, buf: &mut Vec<u8>) {
        for chunk in self.0.iter() {
            chunk.encode(buf);
        }
    }

    fn load_unknown_fields(&mut self, unknowns: Vec<u8>) {
        self.0.push(Chunk::from_encoded(unknowns))
    }

    fn load_field(
        &mut self,
        tag: u32,
        descriptor: &FieldDescriptor,
        value: &PyAny,
    ) -> EncodeResult<()> {
        match &descriptor.attribute {
            FieldAttribute::Repeated => {
                if !self.try_load_packed(tag, &descriptor.value_type, value)? {
                    for value in value.downcast::<PyList>()?.iter() {
                        self.load_single::<false>(tag, &descriptor.value_type, value)?;
                    }
                }
            }
            FieldAttribute::Map(key_type) => {
                for (key, value) in value.downcast::<PyDict>()?.iter() {
                    self.load_map_entry(tag, key_type, &descriptor.value_type, key, value)?;
                }
            }
            FieldAttribute::None => self.load_single::<true>(tag, &descriptor.value_type, value)?,
            _ => self.load_single::<false>(tag, &descriptor.value_type, value)?,
        }

        Ok(())
    }

    fn load_single<const SKIP_DEFAULT: bool>(
        &mut self,
        tag: u32,
        proto_type: &ProtoType,
        value: &PyAny,
    ) -> EncodeResult<()> {
        let py = value.py();
        let chunk = match proto_type {
            ProtoType::Bool => {
                let value: bool = value.extract()?;
                if SKIP_DEFAULT && !value {
                    return Ok(());
                }
                Chunk::from_encoder(tag, &value, enc::bool::encoded_len, enc::bool::encode)?
            }
            ProtoType::Bytes => {
                let value: Vec<u8> = value.extract()?;
                if SKIP_DEFAULT && value.is_empty() {
                    return Ok(());
                }
                Chunk::from_encoder(tag, &value, enc::bytes::encoded_len, enc::bytes::encode)?
            }
            ProtoType::Double => {
                let value: f64 = value.extract()?;
                if SKIP_DEFAULT && value == 0.0 {
                    return Ok(());
                }
                Chunk::from_encoder(tag, &value, enc::double::encoded_len, enc::double::encode)?
            }
            ProtoType::Float => {
                let value: f32 = value.extract()?;
                if SKIP_DEFAULT && value == 0.0 {
                    return Ok(());
                }
                Chunk::from_encoder(tag, &value, enc::float::encoded_len, enc::float::encode)?
            }
            ProtoType::Fixed32 => {
                let value: u32 = value.extract()?;
                if SKIP_DEFAULT && value == 0 {
                    return Ok(());
                }
                Chunk::from_encoder(tag, &value, enc::fixed32::encoded_len, enc::fixed32::encode)?
            }
            ProtoType::Fixed64 => {
                let value: u64 = value.extract()?;
                if SKIP_DEFAULT && value == 0 {
                    return Ok(());
                }
                Chunk::from_encoder(tag, &value, enc::fixed64::encoded_len, enc::fixed64::encode)?
            }
            ProtoType::Int32 => {
                let value: i32 = value.extract()?;
                if SKIP_DEFAULT && value == 0 {
                    return Ok(());
                }
                Chunk::from_encoder(tag, &value, enc::int32::encoded_len, enc::int32::encode)?
            }
            ProtoType::Int64 => {
                let value: i64 = value.extract()?;
                if SKIP_DEFAULT && value == 0 {
                    return Ok(());
                }
                Chunk::from_encoder(tag, &value, enc::int64::encoded_len, enc::int64::encode)?
            }
            ProtoType::Sfixed32 => {
                let value: i32 = value.extract()?;
                if SKIP_DEFAULT && value == 0 {
                    return Ok(());
                }
                Chunk::from_encoder(
                    tag,
                    &value,
                    enc::sfixed32::encoded_len,
                    enc::sfixed32::encode,
                )?
            }
            ProtoType::Sfixed64 => {
                let value: i64 = value.extract()?;
                if SKIP_DEFAULT && value == 0 {
                    return Ok(());
                }
                Chunk::from_encoder(
                    tag,
                    &value,
                    enc::sfixed64::encoded_len,
                    enc::sfixed64::encode,
                )?
            }
            ProtoType::Sint32 => {
                let value: i32 = value.extract()?;
                if SKIP_DEFAULT && value == 0 {
                    return Ok(());
                }
                Chunk::from_encoder(tag, &value, enc::sint32::encoded_len, enc::sint32::encode)?
            }
            ProtoType::Sint64 => {
                let value: i64 = value.extract()?;
                if SKIP_DEFAULT && value == 0 {
                    return Ok(());
                }
                Chunk::from_encoder(tag, &value, enc::sint64::encoded_len, enc::sint64::encode)?
            }
            ProtoType::String => {
                let value: String = value.extract()?;
                if SKIP_DEFAULT && value.is_empty() {
                    return Ok(());
                }
                Chunk::from_encoder(tag, &value, enc::string::encoded_len, enc::string::encode)?
            }
            ProtoType::Uint32 => {
                let value: u32 = value.extract()?;
                if SKIP_DEFAULT && value == 0 {
                    return Ok(());
                }
                Chunk::from_encoder(tag, &value, enc::uint32::encoded_len, enc::uint32::encode)?
            }
            ProtoType::Uint64 => {
                let value: u64 = value.extract()?;
                if SKIP_DEFAULT && value == 0 {
                    return Ok(());
                }
                Chunk::from_encoder(tag, &value, enc::uint64::encoded_len, enc::uint64::encode)?
            }
            ProtoType::Enum(_) => {
                let value: i32 = value
                    .getattr(intern!(py, "value"))
                    .unwrap_or(value)
                    .extract()?;
                if SKIP_DEFAULT && value == 0 {
                    return Ok(());
                }
                Chunk::from_encoder(tag, &value, enc::int32::encoded_len, enc::int32::encode)?
            }
            ProtoType::CustomMessage(cls) => {
                let msg: BetterprotoMessage = value.extract()?;
                if SKIP_DEFAULT && !msg.should_be_serialized()? {
                    return Ok(());
                }
                Chunk::from_message(
                    tag,
                    MessageEncoder::from_betterproto_msg(msg, cls.descriptor(py)?)?,
                )
            }
            ProtoType::BoolValue => Chunk::from_known_message::<BoolValue>(tag, value.extract()?)?,
            ProtoType::BytesValue => {
                Chunk::from_known_message::<BytesValue>(tag, value.extract()?)?
            }
            ProtoType::DoubleValue => {
                Chunk::from_known_message::<DoubleValue>(tag, value.extract()?)?
            }
            ProtoType::FloatValue => {
                Chunk::from_known_message::<FloatValue>(tag, value.extract()?)?
            }
            ProtoType::Int32Value => {
                Chunk::from_known_message::<Int32Value>(tag, value.extract()?)?
            }
            ProtoType::Int64Value => {
                Chunk::from_known_message::<Int64Value>(tag, value.extract()?)?
            }
            ProtoType::UInt32Value => {
                Chunk::from_known_message::<UInt32Value>(tag, value.extract()?)?
            }
            ProtoType::UInt64Value => {
                Chunk::from_known_message::<UInt64Value>(tag, value.extract()?)?
            }
            ProtoType::StringValue => {
                Chunk::from_known_message::<StringValue>(tag, value.extract()?)?
            }
            ProtoType::Timestamp => {
                let msg: Timestamp = value.extract()?;
                if SKIP_DEFAULT && msg.encoded_len() == 0 {
                    return Ok(());
                }
                Chunk::from_known_message(tag, msg)?
            }
            ProtoType::Duration => {
                let msg: Duration = value.extract()?;
                if SKIP_DEFAULT && msg.encoded_len() == 0 {
                    return Ok(());
                }
                Chunk::from_known_message(tag, msg)?
            }
        };

        self.0.push(chunk);
        Ok(())
    }

    fn try_load_packed(
        &mut self,
        tag: u32,
        proto_type: &ProtoType,
        value: &PyAny,
    ) -> EncodeResult<bool> {
        let chunk = match proto_type {
            ProtoType::Bool => Some(Chunk::from_encoder(
                tag,
                value.extract::<Vec<_>>()?.as_ref(),
                enc::bool::encoded_len_packed,
                enc::bool::encode_packed,
            )?),
            ProtoType::Double => Some(Chunk::from_encoder(
                tag,
                value.extract::<Vec<_>>()?.as_ref(),
                enc::double::encoded_len_packed,
                enc::double::encode_packed,
            )?),
            ProtoType::Float => Some(Chunk::from_encoder(
                tag,
                value.extract::<Vec<_>>()?.as_ref(),
                enc::float::encoded_len_packed,
                enc::float::encode_packed,
            )?),
            ProtoType::Fixed32 => Some(Chunk::from_encoder(
                tag,
                value.extract::<Vec<_>>()?.as_ref(),
                enc::fixed32::encoded_len_packed,
                enc::fixed32::encode_packed,
            )?),
            ProtoType::Fixed64 => Some(Chunk::from_encoder(
                tag,
                value.extract::<Vec<_>>()?.as_ref(),
                enc::fixed64::encoded_len_packed,
                enc::fixed64::encode_packed,
            )?),
            ProtoType::Sfixed32 => Some(Chunk::from_encoder(
                tag,
                value.extract::<Vec<_>>()?.as_ref(),
                enc::sfixed32::encoded_len_packed,
                enc::sfixed32::encode_packed,
            )?),
            ProtoType::Sfixed64 => Some(Chunk::from_encoder(
                tag,
                value.extract::<Vec<_>>()?.as_ref(),
                enc::sfixed64::encoded_len_packed,
                enc::sfixed64::encode_packed,
            )?),
            ProtoType::Int32 => Some(Chunk::from_encoder(
                tag,
                value.extract::<Vec<_>>()?.as_ref(),
                enc::int32::encoded_len_packed,
                enc::int32::encode_packed,
            )?),
            ProtoType::Int64 => Some(Chunk::from_encoder(
                tag,
                value.extract::<Vec<_>>()?.as_ref(),
                enc::int64::encoded_len_packed,
                enc::int64::encode_packed,
            )?),
            ProtoType::Uint32 => Some(Chunk::from_encoder(
                tag,
                value.extract::<Vec<_>>()?.as_ref(),
                enc::uint32::encoded_len_packed,
                enc::uint32::encode_packed,
            )?),
            ProtoType::Uint64 => Some(Chunk::from_encoder(
                tag,
                value.extract::<Vec<_>>()?.as_ref(),
                enc::uint64::encoded_len_packed,
                enc::uint64::encode_packed,
            )?),
            ProtoType::Sint32 => Some(Chunk::from_encoder(
                tag,
                value.extract::<Vec<_>>()?.as_ref(),
                enc::sint32::encoded_len_packed,
                enc::sint32::encode_packed,
            )?),
            ProtoType::Sint64 => Some(Chunk::from_encoder(
                tag,
                value.extract::<Vec<_>>()?.as_ref(),
                enc::sint64::encoded_len_packed,
                enc::sint64::encode_packed,
            )?),
            ProtoType::Enum(_) => Some(Chunk::from_encoder(
                tag,
                value
                    .downcast::<PyList>()?
                    .iter()
                    .map(|x| {
                        x.getattr(intern!(x.py(), "value"))
                            .unwrap_or(x)
                            .extract::<i32>()
                    })
                    .collect::<PyResult<Vec<i32>>>()?
                    .as_ref(),
                enc::int32::encoded_len_packed,
                enc::int32::encode_packed,
            )?),
            _ => None,
        };

        match chunk {
            Some(chunk) => {
                self.0.push(chunk);
                Ok(true)
            }
            _ => Ok(false),
        }
    }

    fn load_map_entry(
        &mut self,
        tag: u32,
        key_type: &ProtoType,
        value_type: &ProtoType,
        key: &PyAny,
        value: &PyAny,
    ) -> EncodeResult<()> {
        let mut encoder = MessageEncoder::new();
        encoder.load_single::<true>(1, key_type, key)?;
        encoder.load_single::<true>(2, value_type, value)?;
        self.0.push(Chunk::from_message(tag, encoder));
        Ok(())
    }
}
