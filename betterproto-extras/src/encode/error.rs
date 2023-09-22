use crate::betterproto_interop::InteropError;
use pyo3::{exceptions::PyRuntimeError, PyDowncastError, PyErr};
use thiserror::Error;

#[derive(Error, Debug)]
pub enum EncodeError {
    #[error("Given object is not a valid betterproto message.")]
    NoBetterprotoMessage(#[from] PyErr),
    #[error("Given object is not a valid betterproto message.")]
    DowncastFailed,
    #[error(transparent)]
    Interop(#[from] InteropError),
    #[error("Given object is not a valid betterproto message.")]
    ProstEncode(#[from] prost::EncodeError),
}

pub type EncodeResult<T> = Result<T, EncodeError>;

impl From<PyDowncastError<'_>> for EncodeError {
    fn from(_: PyDowncastError) -> Self {
        Self::DowncastFailed
    }
}

impl From<EncodeError> for PyErr {
    fn from(value: EncodeError) -> Self {
        PyRuntimeError::new_err(value.to_string())
    }
}
