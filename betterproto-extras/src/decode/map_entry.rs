use super::{value::ValueBuilder, DecodeError, DecodeResult, MessageBuilder};
use crate::descriptors::ProtoType;
use prost::{bytes::Buf, encoding::decode_key};
use pyo3::{PyObject, Python};

pub struct MapEntryBuilder<'a, 'py> {
    key: ValueBuilder<'a, 'py>,
    value: ValueBuilder<'a, 'py>,
}

impl<'a, 'py> MapEntryBuilder<'a, 'py> {
    pub fn new(py: Python<'py>, key_type: &'a ProtoType, value_type: &'a ProtoType) -> Self {
        Self {
            key: ValueBuilder::new(py, key_type),
            value: ValueBuilder::new(py, value_type),
        }
    }

    pub fn into_tuple(self) -> DecodeResult<(PyObject, PyObject)> {
        Ok((
            self.key.into_object_or_default()?,
            self.value.into_object_or_default()?,
        ))
    }
}

impl MessageBuilder for MapEntryBuilder<'_, '_> {
    fn parse_next_field(&mut self, buf: &mut impl Buf) -> DecodeResult<()> {
        let (tag, wire_type) = decode_key(buf)?;
        match tag {
            1 => self.key.parse_next_single(wire_type, buf)?,
            2 => self.value.parse_next_single(wire_type, buf)?,
            _ => Err(DecodeError::InvalidMapEntryTag)?,
        }
        Ok(())
    }
}
