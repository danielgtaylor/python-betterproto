use std::collections::HashMap;

use pyo3::{
    types::{PyDict, PyList, PyType},
    FromPyObject, PyAny, Python,
};

use crate::descriptors::MessageDescriptor;

use super::{
    error::{InteropError, InteropResult},
    field_meta::BetterprotoFieldMeta,
};

#[derive(FromPyObject)]
pub struct BetterprotoMessageMeta<'py> {
    pub cls_by_field: HashMap<String, &'py PyType>,
    pub meta_by_field_name: &'py PyDict,
    pub oneof_group_by_field: HashMap<String, String>,
    pub default_gen: HashMap<String, &'py PyAny>,
}

impl<'py> BetterprotoMessageMeta<'py> {
    pub fn is_list_field(&self, field_name: &str) -> InteropResult<bool> {
        let cls = self
            .default_gen
            .get(field_name)
            .ok_or(InteropError::IncompleteMetadata)?;
        Ok(cls.is(cls.py().get_type::<PyList>()))
    }

    pub fn get_class(&self, field_name: &str) -> InteropResult<&'py PyType> {
        let cls = self
            .cls_by_field
            .get(field_name)
            .ok_or(InteropError::IncompleteMetadata)?;
        Ok(cls)
    }

    pub fn into_descriptor(self, py: Python) -> InteropResult<MessageDescriptor> {
        let fields = self
            .meta_by_field_name
            .iter()
            .map(|(name, meta)| {
                let name = name.extract::<String>()?;
                let meta = meta.extract::<BetterprotoFieldMeta>()?;
                Ok((meta.number, meta.into_descriptor(py, name.into(), &self)?))
            })
            .collect::<InteropResult<Vec<_>>>()?;
        Ok(MessageDescriptor { fields })
    }
}
