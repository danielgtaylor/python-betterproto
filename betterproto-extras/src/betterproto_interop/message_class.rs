use super::{
    error::InteropResult, message::BetterprotoMessage, message_meta::BetterprotoMessageMeta,
};
use crate::descriptors::MessageDescriptor;
use pyo3::{pyclass, types::PyType, FromPyObject, Py, PyCell, Python};

#[derive(FromPyObject, Debug)]
pub struct BetterprotoMessageClass(pub(super) Py<PyType>);

impl BetterprotoMessageClass {
    pub fn create_instance<'py>(
        &'py self,
        py: Python<'py>,
    ) -> InteropResult<BetterprotoMessage<'py>> {
        Ok(BetterprotoMessage(self.0.as_ref(py).call0()?))
    }

    pub fn descriptor<'py>(&'py self, py: Python<'py>) -> InteropResult<&'py MessageDescriptor> {
        let cls = self.0.as_ref(py);
        if let Ok(attr) = cls.getattr("_betterproto_extras") {
            if let Ok(cell) = attr.downcast::<PyCell<DescriptorWrapper>>() {
                return Ok(&cell.get().0);
            }
        }

        let desc = cls
            .call0()?
            .getattr("_betterproto")?
            .extract::<BetterprotoMessageMeta>()?
            .into_descriptor(py)?;
        let cell = PyCell::new(py, DescriptorWrapper(desc))?;
        cls.setattr("_betterproto_extras", cell)?;
        Ok(&cell.get().0)
    }
}

#[pyclass(frozen)]
struct DescriptorWrapper(MessageDescriptor);
