use super::{
    error::{DecodeError, DecodeResult},
    field::FieldBuilder,
    MessageBuilder,
};
use crate::{
    betterproto_interop::{BetterprotoMessage, InteropResult},
    descriptors::MessageDescriptor,
    Str,
};
use prost::{
    bytes::{Buf, Bytes},
    encoding::{self as enc, decode_key, WireType},
};
use pyo3::Python;
use std::collections::HashMap;

pub struct CustomMessageBuilder<'a, 'py> {
    fields: HashMap<u32, FieldBuilder<'a, 'py>>,
    active_groups: HashMap<Str, u32>,
    unknown_fields: Vec<u8>,
}

impl<'a, 'py> CustomMessageBuilder<'a, 'py> {
    pub fn new(py: Python<'py>, descriptor: &'a MessageDescriptor) -> Self {
        Self {
            fields: descriptor
                .fields
                .iter()
                .map(|(tag, descriptor)| (*tag, FieldBuilder::new(py, descriptor)))
                .collect(),
            active_groups: HashMap::new(),
            unknown_fields: Vec::new(),
        }
    }

    pub fn merge_into(self, msg: BetterprotoMessage) -> InteropResult<()> {
        for (name, value) in self
            .fields
            .into_values()
            .filter_map(|field| field.into_result())
        {
            msg.set_field(name, value)?;
        }
        msg.append_unknown_fields(self.unknown_fields)?;
        msg.set_deserialized()?;
        Ok(())
    }

    pub fn parse_next_unknown(
        &mut self,
        tag: u32,
        wire_type: WireType,
        buf: &mut impl Buf,
    ) -> DecodeResult<()> {
        enc::encode_key(tag, wire_type, &mut self.unknown_fields);
        match wire_type {
            WireType::Varint => {
                let value = enc::decode_varint(buf)?;
                enc::encode_varint(value, &mut self.unknown_fields);
            }
            WireType::SixtyFourBit => {
                let mut value = [0; 8];
                if buf.remaining() < value.len() {
                    return Err(DecodeError::InvalidData);
                }
                buf.copy_to_slice(&mut value);
                self.unknown_fields.extend_from_slice(&value);
            }
            WireType::LengthDelimited => {
                let mut value = Bytes::default();
                enc::bytes::merge(wire_type, &mut value, buf, Default::default())?;
                enc::encode_varint(value.len() as u64, &mut self.unknown_fields);
                self.unknown_fields.extend(value);
            }
            WireType::ThirtyTwoBit => {
                let mut value = [0; 4];
                if buf.remaining() < value.len() {
                    return Err(DecodeError::InvalidData);
                }
                buf.copy_to_slice(&mut value);
                self.unknown_fields.extend_from_slice(&value);
            }
            _ => return Err(DecodeError::InvalidData),
        };

        Ok(())
    }
}

impl MessageBuilder for CustomMessageBuilder<'_, '_> {
    fn parse_next_field(&mut self, buf: &mut impl Buf) -> DecodeResult<()> {
        let (tag, wire_type) = decode_key(buf)?;
        let group = match self.fields.get_mut(&tag) {
            Some(builder) => {
                builder.parse_next(wire_type, buf)?;
                builder.group()
            }
            None => {
                self.parse_next_unknown(tag, wire_type, buf)?;
                None
            }
        };
        if let Some(group) = group {
            if let Some(previous_tag) = self.active_groups.insert(group, tag) {
                if previous_tag != tag {
                    self.fields
                        .get_mut(&previous_tag)
                        .expect("Field exists")
                        .reset()
                }
            }
        }
        Ok(())
    }
}
