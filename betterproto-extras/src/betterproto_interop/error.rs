use pyo3::PyErr;
use thiserror::Error;

#[derive(Error, Debug)]
pub enum InteropError {
    #[error("Given object is not a valid betterproto message.")]
    NoBetterprotoMessage(#[from] PyErr),
    #[error("Unsupported value type `{0}`.")]
    UnsupportedValueType(String),
    #[error("Unsupported key type `{0:?}`.")]
    UnsupportedKeyType(String),
    #[error("Unsupported wrapped type `{0:?}`.")]
    UnsupportedWrappedType(String),
    #[error("Given object is not a valid betterproto message.")]
    IncompleteMetadata,
}

pub type InteropResult<T> = Result<T, InteropError>;
