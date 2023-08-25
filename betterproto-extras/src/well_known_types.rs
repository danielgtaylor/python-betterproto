use indoc::indoc;
use prost::Message;
use pyo3::{
    sync::GILOnceCell,
    types::{PyBytes, PyModule},
    FromPyObject, PyAny, PyObject, PyResult, Python, ToPyObject,
};

#[derive(Message)]
pub struct BoolValue {
    #[prost(bool, tag = "1")]
    pub value: bool,
}

#[derive(Message)]
pub struct BytesValue {
    #[prost(bytes, tag = "1")]
    pub value: Vec<u8>,
}

#[derive(Message)]
pub struct DoubleValue {
    #[prost(double, tag = "1")]
    pub value: f64,
}

#[derive(Message)]
pub struct FloatValue {
    #[prost(float, tag = "1")]
    pub value: f32,
}

#[derive(Message)]
pub struct Int32Value {
    #[prost(int32, tag = "1")]
    pub value: i32,
}

#[derive(Message)]
pub struct Int64Value {
    #[prost(int64, tag = "1")]
    pub value: i64,
}

#[derive(Message)]
pub struct UInt32Value {
    #[prost(uint32, tag = "1")]
    pub value: u32,
}

#[derive(Message)]
pub struct UInt64Value {
    #[prost(uint64, tag = "1")]
    pub value: u64,
}

#[derive(Message)]
pub struct StringValue {
    #[prost(string, tag = "1")]
    pub value: String,
}

#[derive(Message)]
pub struct Duration {
    #[prost(int64, tag = "1")]
    pub seconds: i64,
    #[prost(int32, tag = "2")]
    pub nanos: i32,
}

#[derive(Message)]
pub struct Timestamp {
    #[prost(int64, tag = "1")]
    pub seconds: i64,
    #[prost(int32, tag = "2")]
    pub nanos: i32,
}

impl<'py> FromPyObject<'py> for BoolValue {
    fn extract(ob: &'py PyAny) -> PyResult<Self> {
        let res = BoolValue {
            value: ob.extract()?,
        };
        Ok(res)
    }
}

impl<'py> FromPyObject<'py> for BytesValue {
    fn extract(ob: &'py PyAny) -> PyResult<Self> {
        let res = BytesValue {
            value: ob.extract()?,
        };
        Ok(res)
    }
}

impl<'py> FromPyObject<'py> for DoubleValue {
    fn extract(ob: &'py PyAny) -> PyResult<Self> {
        let res = DoubleValue {
            value: ob.extract()?,
        };
        Ok(res)
    }
}

impl<'py> FromPyObject<'py> for FloatValue {
    fn extract(ob: &'py PyAny) -> PyResult<Self> {
        let res = FloatValue {
            value: ob.extract()?,
        };
        Ok(res)
    }
}

impl<'py> FromPyObject<'py> for Int32Value {
    fn extract(ob: &'py PyAny) -> PyResult<Self> {
        let res = Int32Value {
            value: ob.extract()?,
        };
        Ok(res)
    }
}

impl<'py> FromPyObject<'py> for Int64Value {
    fn extract(ob: &'py PyAny) -> PyResult<Self> {
        let res = Int64Value {
            value: ob.extract()?,
        };
        Ok(res)
    }
}

impl<'py> FromPyObject<'py> for UInt32Value {
    fn extract(ob: &'py PyAny) -> PyResult<Self> {
        let res = UInt32Value {
            value: ob.extract()?,
        };
        Ok(res)
    }
}

impl<'py> FromPyObject<'py> for UInt64Value {
    fn extract(ob: &'py PyAny) -> PyResult<Self> {
        let res = UInt64Value {
            value: ob.extract()?,
        };
        Ok(res)
    }
}

impl<'py> FromPyObject<'py> for StringValue {
    fn extract(ob: &'py PyAny) -> PyResult<Self> {
        let res = StringValue {
            value: ob.extract()?,
        };
        Ok(res)
    }
}

impl<'py> FromPyObject<'py> for Duration {
    fn extract(ob: &'py PyAny) -> PyResult<Self> {
        let py = ob.py();
        static DECONSTRUCTOR_CACHE: GILOnceCell<PyObject> = GILOnceCell::new();
        let deconstructor = DECONSTRUCTOR_CACHE
            .get_or_init(py, || {
                PyModule::from_code(
                    py,
                    indoc! {"
                        from datetime import timedelta
                        
                        def deconstructor(delta, *, _1_microsecond = timedelta(microseconds=1)):
                            total_ms = delta // _1_microsecond
                            seconds = int(total_ms / 1e6)
                            nanos = int((total_ms % 1e6) * 1e3)
                            return (seconds, nanos)
                    "},
                    "",
                    "",
                )
                .expect("This is a valid Python module")
                .getattr("deconstructor")
                .expect("Attribute exists")
                .to_object(py)
            })
            .as_ref(py);
        let (seconds, nanos) = deconstructor.call1((ob,))?.extract()?;
        let res = Duration { seconds, nanos };
        Ok(res)
    }
}

impl<'py> FromPyObject<'py> for Timestamp {
    fn extract(ob: &'py PyAny) -> PyResult<Self> {
        let py = ob.py();
        static DECONSTRUCTOR_CACHE: GILOnceCell<PyObject> = GILOnceCell::new();
        let deconstructor = DECONSTRUCTOR_CACHE
            .get_or_init(py, || {
                PyModule::from_code(
                    py,
                    indoc! {"
                        def deconstructor(dt):
                            seconds = int(dt.timestamp())
                            nanos = int(dt.microsecond * 1e3)
                            return (seconds, nanos)
                    "},
                    "",
                    "",
                )
                .expect("This is a valid Python module")
                .getattr("deconstructor")
                .expect("Attribute exists")
                .to_object(py)
            })
            .as_ref(py);
        let (seconds, nanos) = deconstructor.call1((ob,))?.extract()?;
        let res = Timestamp { seconds, nanos };
        Ok(res)
    }
}

impl ToPyObject for BoolValue {
    fn to_object(&self, py: Python) -> PyObject {
        self.value.to_object(py)
    }
}

impl ToPyObject for BytesValue {
    fn to_object(&self, py: Python) -> PyObject {
        PyBytes::new(py, &self.value).to_object(py)
    }
}

impl ToPyObject for DoubleValue {
    fn to_object(&self, py: Python) -> PyObject {
        self.value.to_object(py)
    }
}

impl ToPyObject for FloatValue {
    fn to_object(&self, py: Python) -> PyObject {
        self.value.to_object(py)
    }
}

impl ToPyObject for Int32Value {
    fn to_object(&self, py: Python) -> PyObject {
        self.value.to_object(py)
    }
}

impl ToPyObject for Int64Value {
    fn to_object(&self, py: Python) -> PyObject {
        self.value.to_object(py)
    }
}

impl ToPyObject for UInt32Value {
    fn to_object(&self, py: Python) -> PyObject {
        self.value.to_object(py)
    }
}

impl ToPyObject for UInt64Value {
    fn to_object(&self, py: Python) -> PyObject {
        self.value.to_object(py)
    }
}

impl ToPyObject for StringValue {
    fn to_object(&self, py: Python) -> PyObject {
        self.value.to_object(py)
    }
}

impl ToPyObject for Duration {
    fn to_object(&self, py: Python) -> PyObject {
        static CONSTRUCTOR_CACHE: GILOnceCell<PyObject> = GILOnceCell::new();
        let constructor = CONSTRUCTOR_CACHE.get_or_init(py, || {
            PyModule::from_code(
                py,
                indoc! {"
                    from datetime import timedelta
                    
                    def constructor(s, ms):
                        return timedelta(seconds=s, microseconds=ms)
                "},
                "",
                "",
            )
            .expect("This is a valid Python module")
            .getattr("constructor")
            .expect("Attribute exists")
            .to_object(py)
        });
        constructor
            .call1(py, (self.seconds as f64, (self.nanos as f64) / 1e3))
            .expect("static function will not fail")
    }
}

impl ToPyObject for Timestamp {
    fn to_object(&self, py: Python) -> PyObject {
        static CONSTRUCTOR_CACHE: GILOnceCell<PyObject> = GILOnceCell::new();
        let constructor = CONSTRUCTOR_CACHE.get_or_init(py, || {
            PyModule::from_code(
                py,
                indoc! {"
                    from datetime import datetime, timezone
                    
                    def constructor(ts):
                        return datetime.fromtimestamp(ts, tz=timezone.utc)
                "},
                "",
                "",
            )
            .expect("This is a valid Python module")
            .getattr("constructor")
            .expect("Attribute exists")
            .to_object(py)
        });
        let ts = (self.seconds as f64) + (self.nanos as f64) / 1e9;
        constructor
            .call1(py, (ts,))
            .expect("static function will not fail")
    }
}
