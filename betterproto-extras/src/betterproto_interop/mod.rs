mod error;
mod field_meta;
mod message;
mod message_class;
mod message_meta;

pub use self::{
    error::{InteropError, InteropResult},
    message::BetterprotoMessage,
    message_class::BetterprotoMessageClass,
};
use pyo3::{
    exceptions::PyValueError, types::PyType, FromPyObject, Py, PyObject, Python, ToPyObject,
};

#[derive(FromPyObject, Debug)]
pub struct BetterprotoEnumClass(Py<PyType>);

impl BetterprotoEnumClass {
    pub fn create_instance(&self, py: Python, x: i32) -> InteropResult<PyObject> {
        let res = self.0.call1(py, (x,)).or_else(|err| {
            if err.is_instance_of::<PyValueError>(py) {
                Ok(x.to_object(py))
            } else {
                Err(err)
            }
        })?;
        Ok(res)
    }
}
