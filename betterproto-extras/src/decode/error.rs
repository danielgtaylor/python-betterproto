use crate::betterproto_interop::InteropError;
use pyo3::{exceptions::PyRuntimeError, PyErr};
use thiserror::Error;

#[derive(Error, Debug)]
pub enum DecodeError {
    #[error(transparent)]
    Interop(#[from] InteropError),
    #[error("The given binary data does not match the protobuf schema.")]
    ProstDecode(#[from] prost::DecodeError),
    #[error("The given binary data does not match the protobuf schema.")]
    MapEntryHasNoKey,
    #[error("The given binary data does not match the protobuf schema.")]
    InvalidMapEntryTag,
    #[error("The given binary data is not a valid protobuf message.")]
    InvalidData,
}

pub type DecodeResult<T> = Result<T, DecodeError>;

impl From<DecodeError> for PyErr {
    fn from(value: DecodeError) -> Self {
        PyRuntimeError::new_err(value.to_string())
    }
}
