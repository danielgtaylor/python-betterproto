use super::{error::InteropResult, BetterprotoMessageClass};
use indoc::indoc;
use pyo3::{
    intern,
    sync::GILOnceCell,
    types::{PyBytes, PyModule},
    FromPyObject, IntoPy, PyAny, PyObject, Python, ToPyObject,
};

#[derive(FromPyObject, Clone, Copy)]
pub struct BetterprotoMessage<'py>(pub(super) &'py PyAny);

impl<'py> BetterprotoMessage<'py> {
    pub fn class(&self) -> BetterprotoMessageClass {
        BetterprotoMessageClass(self.0.get_type().into_py(self.0.py()))
    }

    pub fn py(&self) -> Python {
        self.0.py()
    }

    pub fn set_field(&self, field_name: &str, value: impl ToPyObject) -> InteropResult<()> {
        self.0.setattr(field_name, value)?;
        Ok(())
    }

    pub fn get_field(&'py self, field_name: &str) -> InteropResult<Option<&'py PyAny>> {
        let py = self.py();
        static GETTER_CACHE: GILOnceCell<PyObject> = GILOnceCell::new();
        let getter = GETTER_CACHE
            .get_or_init(py, || {
                PyModule::from_code(
                    py,
                    indoc! {"
                        from betterproto import PLACEHOLDER

                        def getter(msg, field_name):
                            value = msg._Message__raw_get(field_name)
                            if value is PLACEHOLDER:
                                return
                            return value
                    "},
                    "",
                    "",
                )
                .expect("This is a valid Python module")
                .getattr("getter")
                .expect("Attribute exists")
                .to_object(py)
            })
            .as_ref(py);

        let res = getter.call1((self.0, field_name))?.extract()?;
        Ok(res)
    }

    pub fn append_unknown_fields(&self, mut data: Vec<u8>) -> InteropResult<()> {
        let attr_name = intern!(self.py(), "_unknown_fields");
        if !data.is_empty() {
            let mut unknown_fields = self.0.getattr(attr_name)?.extract::<Vec<u8>>()?;
            unknown_fields.append(&mut data);
            self.0
                .setattr(attr_name, PyBytes::new(self.py(), &unknown_fields))?;
        }
        Ok(())
    }

    pub fn get_unknown_fields(&self) -> InteropResult<Vec<u8>> {
        Ok(self
            .0
            .getattr(intern!(self.py(), "_unknown_fields"))?
            .extract()?)
    }

    pub fn set_deserialized(&self) -> InteropResult<()> {
        self.0
            .setattr(intern!(self.py(), "_serialized_on_wire"), true)?;
        Ok(())
    }

    pub fn should_be_serialized(&self) -> InteropResult<bool> {
        let res = self
            .0
            .getattr(intern!(self.py(), "_serialized_on_wire"))?
            .extract()?;
        Ok(res)
    }
}

impl ToPyObject for BetterprotoMessage<'_> {
    fn to_object(&self, py: Python<'_>) -> pyo3::PyObject {
        self.0.to_object(py)
    }
}
