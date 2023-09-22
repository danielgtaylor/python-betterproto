use super::{
    error::{InteropError, InteropResult},
    message_class::BetterprotoMessageClass,
    message_meta::BetterprotoMessageMeta,
    BetterprotoEnumClass,
};
use crate::{
    descriptors::{FieldAttribute, FieldDescriptor, ProtoType},
    Str,
};
use pyo3::{FromPyObject, IntoPy, Python};

#[derive(FromPyObject)]
pub struct BetterprotoFieldMeta {
    pub number: u32,
    pub map_types: Option<(String, String)>,
    pub proto_type: String,
    pub wraps: Option<String>,
    pub optional: bool,
}

impl BetterprotoFieldMeta {
    pub fn into_descriptor(
        self,
        py: Python,
        field_name: Str,
        msg_meta: &BetterprotoMessageMeta,
    ) -> InteropResult<FieldDescriptor> {
        if let Some((key_type, value_type)) = self.map_types {
            let key_type = convert_key_type(&key_type)?;
            let value_type =
                convert_value_type(py, &value_type, &format!("{field_name}.value"), msg_meta)?;
            return Ok(FieldDescriptor {
                name: field_name,
                attribute: FieldAttribute::Map(key_type),
                value_type,
            });
        }

        let value_type = match self.wraps {
            Some(wrapped_type) => convert_wrapped_type(&wrapped_type)?,
            None => convert_value_type(py, &self.proto_type, &field_name, msg_meta)?,
        };

        let attribute = if self.optional {
            FieldAttribute::Optional
        } else if let Some(group) = msg_meta.oneof_group_by_field.get(field_name.as_ref()) {
            FieldAttribute::Group(Str::from(group.as_ref()))
        } else if msg_meta.is_list_field(&field_name)? {
            FieldAttribute::Repeated
        } else {
            FieldAttribute::None
        };

        Ok(FieldDescriptor {
            name: field_name,
            value_type,
            attribute,
        })
    }
}

fn convert_value_type(
    py: Python,
    type_name: &str,
    field_name: &str,
    msg_meta: &BetterprotoMessageMeta,
) -> InteropResult<ProtoType> {
    match type_name {
        "bool" => Ok(ProtoType::Bool),
        "int32" => Ok(ProtoType::Int32),
        "int64" => Ok(ProtoType::Int64),
        "uint32" => Ok(ProtoType::Uint32),
        "uint64" => Ok(ProtoType::Uint64),
        "sint32" => Ok(ProtoType::Sint32),
        "sint64" => Ok(ProtoType::Sint64),
        "float" => Ok(ProtoType::Float),
        "double" => Ok(ProtoType::Double),
        "fixed32" => Ok(ProtoType::Fixed32),
        "sfixed32" => Ok(ProtoType::Sfixed32),
        "fixed64" => Ok(ProtoType::Fixed64),
        "sfixed64" => Ok(ProtoType::Sfixed64),
        "string" => Ok(ProtoType::String),
        "bytes" => Ok(ProtoType::Bytes),
        "enum" => Ok(ProtoType::Enum(BetterprotoEnumClass(
            msg_meta.get_class(field_name)?.into_py(py),
        ))),
        "message" => {
            let cls = msg_meta.get_class(field_name)?;
            if cls.getattr("__module__")?.extract::<&str>()? == "datetime" {
                match cls.name()? {
                    "datetime" => return Ok(ProtoType::Timestamp),
                    "timedelta" => return Ok(ProtoType::Duration),
                    _ => {}
                }
            }
            Ok(ProtoType::CustomMessage(BetterprotoMessageClass(
                cls.into_py(py),
            )))
        }
        _ => Err(InteropError::UnsupportedValueType(type_name.to_string())),
    }
}

fn convert_key_type(type_name: &str) -> InteropResult<ProtoType> {
    match type_name {
        "bool" => Ok(ProtoType::Bool),
        "int32" => Ok(ProtoType::Int32),
        "int64" => Ok(ProtoType::Int64),
        "uint32" => Ok(ProtoType::Uint32),
        "uint64" => Ok(ProtoType::Uint64),
        "sint32" => Ok(ProtoType::Sint32),
        "sint64" => Ok(ProtoType::Sint64),
        "fixed32" => Ok(ProtoType::Fixed32),
        "sfixed32" => Ok(ProtoType::Sfixed32),
        "fixed64" => Ok(ProtoType::Fixed64),
        "sfixed64" => Ok(ProtoType::Sfixed64),
        "string" => Ok(ProtoType::String),
        _ => Err(InteropError::UnsupportedKeyType(type_name.to_string())),
    }
}

fn convert_wrapped_type(type_name: &str) -> InteropResult<ProtoType> {
    match type_name {
        "bool" => Ok(ProtoType::BoolValue),
        "int32" => Ok(ProtoType::Int32Value),
        "int64" => Ok(ProtoType::Int64Value),
        "uint32" => Ok(ProtoType::UInt32Value),
        "uint64" => Ok(ProtoType::UInt64Value),
        "float" => Ok(ProtoType::FloatValue),
        "double" => Ok(ProtoType::DoubleValue),
        "string" => Ok(ProtoType::StringValue),
        "bytes" => Ok(ProtoType::BytesValue),
        _ => Err(InteropError::UnsupportedWrappedType(type_name.to_string())),
    }
}
