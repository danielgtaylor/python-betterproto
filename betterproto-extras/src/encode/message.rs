use crate::{
    betterproto_interop::BetterprotoMessage,
    descriptors::{Cardinality, FieldDescriptor, MessageDescriptor, ProtoType},
    well_known_types::{
        BoolValue, BytesValue, DoubleValue, Duration, FloatValue, Int32Value, Int64Value,
        StringValue, Timestamp, UInt32Value, UInt64Value,
    },
};
use prost::encoding as enc;
use pyo3::{
    types::{PyDict, PyList},
    PyAny,
};

use super::{chunk::Chunk, EncodeResult};

pub struct MessageEncoder(Vec<Chunk>);

impl MessageEncoder {
    pub fn from_betterproto_msg(
        msg: BetterprotoMessage,
        descriptor: &MessageDescriptor,
    ) -> EncodeResult<Self> {
        let mut encoder = MessageEncoder::new();
        for (tag, field) in descriptor.fields.iter() {
            if let Some(value) = msg.get_relevant_field(&field.name)? {
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
        match &descriptor.cardinality {
            Cardinality::Single => self.load_single(tag, &descriptor.value_type, value)?,
            Cardinality::Repeated => {
                if !self.try_load_packed(tag, &descriptor.value_type, value)? {
                    for value in value.downcast::<PyList>()?.iter() {
                        self.load_single(tag, &descriptor.value_type, value)?;
                    }
                }
            }
            Cardinality::Map(key_type) => {
                for (key, value) in value.downcast::<PyDict>()?.iter() {
                    self.load_map_entry(tag, key_type, &descriptor.value_type, key, value)?;
                }
            }
        }

        Ok(())
    }

    fn load_single(&mut self, tag: u32, proto_type: &ProtoType, value: &PyAny) -> EncodeResult<()> {
        let py = value.py();
        let chunk = match proto_type {
            ProtoType::Bool => {
                Chunk::from_single_encoder(tag, value, enc::bool::encoded_len, enc::bool::encode)?
            }
            ProtoType::Bytes => Chunk::from_single_encoder::<Vec<u8>>(
                tag,
                value,
                enc::bytes::encoded_len,
                enc::bytes::encode,
            )?,
            ProtoType::Double => Chunk::from_single_encoder(
                tag,
                value,
                enc::double::encoded_len,
                enc::double::encode,
            )?,
            ProtoType::Float => {
                Chunk::from_single_encoder(tag, value, enc::float::encoded_len, enc::float::encode)?
            }
            ProtoType::Fixed32 => Chunk::from_single_encoder(
                tag,
                value,
                enc::fixed32::encoded_len,
                enc::fixed32::encode,
            )?,
            ProtoType::Fixed64 => Chunk::from_single_encoder(
                tag,
                value,
                enc::fixed64::encoded_len,
                enc::fixed64::encode,
            )?,
            ProtoType::Int32 => {
                Chunk::from_single_encoder(tag, value, enc::int32::encoded_len, enc::int32::encode)?
            }
            ProtoType::Int64 => {
                Chunk::from_single_encoder(tag, value, enc::int64::encoded_len, enc::int64::encode)?
            }
            ProtoType::Sfixed32 => Chunk::from_single_encoder(
                tag,
                value,
                enc::sfixed32::encoded_len,
                enc::sfixed32::encode,
            )?,
            ProtoType::Sfixed64 => Chunk::from_single_encoder(
                tag,
                value,
                enc::sfixed64::encoded_len,
                enc::sfixed64::encode,
            )?,
            ProtoType::Sint32 => Chunk::from_single_encoder(
                tag,
                value,
                enc::sint32::encoded_len,
                enc::sint32::encode,
            )?,
            ProtoType::Sint64 => Chunk::from_single_encoder(
                tag,
                value,
                enc::sint64::encoded_len,
                enc::sint64::encode,
            )?,
            ProtoType::String => Chunk::from_single_encoder(
                tag,
                value,
                enc::string::encoded_len,
                enc::string::encode,
            )?,
            ProtoType::Uint32 => Chunk::from_single_encoder(
                tag,
                value,
                enc::uint32::encoded_len,
                enc::uint32::encode,
            )?,
            ProtoType::Uint64 => Chunk::from_single_encoder(
                tag,
                value,
                enc::uint64::encoded_len,
                enc::uint64::encode,
            )?,
            ProtoType::Enum(_) => {
                let value = value.getattr("value").unwrap_or(value);
                Chunk::from_single_encoder(tag, value, enc::int32::encoded_len, enc::int32::encode)?
            }
            ProtoType::CustomMessage(cls) => Chunk::from_message(
                tag,
                MessageEncoder::from_betterproto_msg(value.extract()?, cls.descriptor(py)?)?,
            ),
            ProtoType::BoolValue => Chunk::from_known_message::<BoolValue>(tag, value)?,
            ProtoType::BytesValue => Chunk::from_known_message::<BytesValue>(tag, value)?,
            ProtoType::DoubleValue => Chunk::from_known_message::<DoubleValue>(tag, value)?,
            ProtoType::FloatValue => Chunk::from_known_message::<FloatValue>(tag, value)?,
            ProtoType::Int32Value => Chunk::from_known_message::<Int32Value>(tag, value)?,
            ProtoType::Int64Value => Chunk::from_known_message::<Int64Value>(tag, value)?,
            ProtoType::UInt32Value => Chunk::from_known_message::<UInt32Value>(tag, value)?,
            ProtoType::UInt64Value => Chunk::from_known_message::<UInt64Value>(tag, value)?,
            ProtoType::StringValue => Chunk::from_known_message::<StringValue>(tag, value)?,
            ProtoType::Timestamp => Chunk::from_known_message::<Timestamp>(tag, value)?,
            ProtoType::Duration => Chunk::from_known_message::<Duration>(tag, value)?,
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
            ProtoType::Bool => Some(Chunk::from_packing_encoder(
                tag,
                value,
                enc::bool::encoded_len_packed,
                enc::bool::encode_packed,
            )?),
            ProtoType::Double => Some(Chunk::from_packing_encoder(
                tag,
                value,
                enc::double::encoded_len_packed,
                enc::double::encode_packed,
            )?),
            ProtoType::Float => Some(Chunk::from_packing_encoder(
                tag,
                value,
                enc::float::encoded_len_packed,
                enc::float::encode_packed,
            )?),
            ProtoType::Fixed32 => Some(Chunk::from_packing_encoder(
                tag,
                value,
                enc::fixed32::encoded_len_packed,
                enc::fixed32::encode_packed,
            )?),
            ProtoType::Fixed64 => Some(Chunk::from_packing_encoder(
                tag,
                value,
                enc::fixed64::encoded_len_packed,
                enc::fixed64::encode_packed,
            )?),
            ProtoType::Sfixed32 => Some(Chunk::from_packing_encoder(
                tag,
                value,
                enc::sfixed32::encoded_len_packed,
                enc::sfixed32::encode_packed,
            )?),
            ProtoType::Sfixed64 => Some(Chunk::from_packing_encoder(
                tag,
                value,
                enc::sfixed64::encoded_len_packed,
                enc::sfixed64::encode_packed,
            )?),
            ProtoType::Int32 => Some(Chunk::from_packing_encoder(
                tag,
                value,
                enc::int32::encoded_len_packed,
                enc::int32::encode_packed,
            )?),
            ProtoType::Int64 => Some(Chunk::from_packing_encoder(
                tag,
                value,
                enc::int64::encoded_len_packed,
                enc::int64::encode_packed,
            )?),
            ProtoType::Uint32 => Some(Chunk::from_packing_encoder(
                tag,
                value,
                enc::uint32::encoded_len_packed,
                enc::uint32::encode_packed,
            )?),
            ProtoType::Uint64 => Some(Chunk::from_packing_encoder(
                tag,
                value,
                enc::uint64::encoded_len_packed,
                enc::uint64::encode_packed,
            )?),
            ProtoType::Sint32 => Some(Chunk::from_packing_encoder(
                tag,
                value,
                enc::sint32::encoded_len_packed,
                enc::sint32::encode_packed,
            )?),
            ProtoType::Sint64 => Some(Chunk::from_packing_encoder(
                tag,
                value,
                enc::sint64::encoded_len_packed,
                enc::sint64::encode_packed,
            )?),
            ProtoType::Enum(_) => Some(Chunk::from_repeated_enum(tag, value)?),
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
        encoder.load_single(1, key_type, key)?;
        encoder.load_single(2, value_type, value)?;
        self.0.push(Chunk::from_message(tag, encoder));
        Ok(())
    }
}
