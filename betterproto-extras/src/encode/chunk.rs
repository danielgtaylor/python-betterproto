use super::{message::MessageEncoder, EncodeResult};
use prost::{bytes::BufMut, encoding as enc, Message};
use pyo3::{types::PyList, FromPyObject, PyAny, PyResult};
use std::ops::Deref;

pub struct Chunk(ChunkVariant);

enum ChunkVariant {
    PreEncoded(Box<[u8]>),
    MessageField(u32, Box<MessageEncoder>),
}

impl Chunk {
    pub fn from_single_encoder<'py, T: FromPyObject<'py>>(
        tag: u32,
        value: &'py PyAny,
        len_fn: impl FnOnce(u32, &T) -> usize,
        encoder: impl FnOnce(u32, &T, &mut Vec<u8>),
    ) -> EncodeResult<Self> {
        Self::from_encoder(tag, value, |x| Ok(x.extract()?), len_fn, encoder)
    }

    pub fn from_packing_encoder<'py, T: FromPyObject<'py>>(
        tag: u32,
        value: &'py PyAny,
        len_fn: impl FnOnce(u32, &[T]) -> usize,
        encoder: impl FnOnce(u32, &[T], &mut Vec<u8>),
    ) -> EncodeResult<Self> {
        Self::from_encoder(
            tag,
            value,
            |x| Ok(x.extract::<Vec<T>>()?),
            |tag, ls| len_fn(tag, ls),
            |tag, ls, buf| encoder(tag, ls, buf),
        )
    }

    pub fn from_repeated_enum(tag: u32, value: &PyAny) -> EncodeResult<Self> {
        Self::from_encoder(
            tag,
            value,
            |value| {
                Ok(value
                    .downcast::<PyList>()?
                    .iter()
                    .map(|x| x.getattr("value").unwrap_or(x).extract::<i32>())
                    .collect::<PyResult<Vec<i32>>>()?)
            },
            |tag, ls| enc::int32::encoded_len_packed(tag, ls),
            |tag, ls, buf| enc::int32::encode_packed(tag, ls, buf),
        )
    }

    pub fn from_encoded(encoded: Vec<u8>) -> Self {
        Self(ChunkVariant::PreEncoded(encoded.into_boxed_slice()))
    }

    pub fn from_known_message<'py, T: Message + FromPyObject<'py>>(
        tag: u32,
        value: &'py PyAny,
    ) -> EncodeResult<Self> {
        let msg = value.extract::<T>()?;
        let msg_len = msg.encoded_len();
        let capacity = msg_len + enc::key_len(tag) + enc::encoded_len_varint(msg_len as u64);
        let mut buf = Vec::with_capacity(capacity);
        enc::encode_key(tag, enc::WireType::LengthDelimited, &mut buf);
        msg.encode_length_delimited(&mut buf)?;
        debug_assert_eq!(capacity, buf.len());
        Ok(Self(ChunkVariant::PreEncoded(buf.into_boxed_slice())))
    }

    pub fn from_message(tag: u32, encoder: MessageEncoder) -> Self {
        Self(ChunkVariant::MessageField(tag, Box::new(encoder)))
    }

    pub fn encoded_len(&self) -> usize {
        match &self.0 {
            ChunkVariant::PreEncoded(bytes) => bytes.len(),
            ChunkVariant::MessageField(tag, msg) => {
                let msg_len = msg.encoded_len();
                let meta_size = enc::key_len(*tag) + enc::encoded_len_varint(msg_len as u64);
                msg_len + meta_size
            }
        }
    }

    pub fn encode(&self, buf: &mut Vec<u8>) {
        match &self.0 {
            ChunkVariant::PreEncoded(bytes) => buf.put_slice(bytes),
            ChunkVariant::MessageField(tag, msg) => {
                enc::encode_key(*tag, enc::WireType::LengthDelimited, buf);
                enc::encode_varint(msg.encoded_len() as u64, buf);
                msg.encode(buf);
            }
        }
    }

    fn from_encoder<'py, T>(
        tag: u32,
        value: &'py PyAny,
        extractor: impl FnOnce(&'py PyAny) -> EncodeResult<T>,
        len_fn: impl FnOnce(u32, &T) -> usize,
        encoder: impl FnOnce(u32, &T, &mut Vec<u8>),
    ) -> EncodeResult<Self> {
        let value = extractor(value)?;
        let capacity = len_fn(tag, (&value).deref());
        let mut buf = Vec::with_capacity(capacity);
        encoder(tag, (&value).deref(), &mut buf);
        debug_assert_eq!(capacity, buf.len());
        Ok(Self(ChunkVariant::PreEncoded(buf.into_boxed_slice())))
    }
}
