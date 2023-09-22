use super::{error::DecodeResult, value::ValueBuilder};
use crate::{
    descriptors::{FieldAttribute, FieldDescriptor},
    Str,
};
use prost::{bytes::Buf, encoding::WireType};
use pyo3::{PyObject, Python};

pub struct FieldBuilder<'a, 'py> {
    descriptor: &'a FieldDescriptor,
    value: ValueBuilder<'a, 'py>,
}

impl<'a, 'py> FieldBuilder<'a, 'py> {
    pub fn new(py: Python<'py>, descriptor: &'a FieldDescriptor) -> Self {
        Self {
            descriptor,
            value: ValueBuilder::new(py, &descriptor.value_type),
        }
    }

    pub fn into_result(self) -> Option<(&'a str, PyObject)> {
        self.value
            .into_object()
            .map(|obj| (self.descriptor.name.as_ref(), obj))
    }

    pub fn group(&self) -> Option<Str> {
        match &self.descriptor.attribute {
            FieldAttribute::Group(name) => Some(name.clone()),
            _ => None,
        }
    }

    pub fn reset(&mut self) {
        self.value.reset()
    }

    pub fn parse_next(&mut self, wire_type: WireType, buf: &mut impl Buf) -> DecodeResult<()> {
        match &self.descriptor.attribute {
            FieldAttribute::Repeated => self.value.parse_next_list_entry(wire_type, buf)?,
            FieldAttribute::Map(key_type) => {
                self.value.parse_next_map_entry(wire_type, key_type, buf)?
            }
            _ => self.value.parse_next_single(wire_type, buf)?,
        }
        Ok(())
    }
}
