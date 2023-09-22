use super::{message::MessageEncoder, EncodeResult};
use prost::{bytes::BufMut, encoding as enc, Message};

pub struct Chunk(ChunkVariant);

enum ChunkVariant {
    PreEncoded(Box<[u8]>),
    MessageField(u32, Box<MessageEncoder>),
}

impl Chunk {
    pub fn from_encoder<T: ?Sized>(
        tag: u32,
        value: &T,
        len_fn: impl FnOnce(u32, &T) -> usize,
        encoder: impl FnOnce(u32, &T, &mut Vec<u8>),
    ) -> EncodeResult<Self> {
        let capacity = len_fn(tag, value);
        let mut buf = Vec::with_capacity(capacity);
        encoder(tag, value, &mut buf);
        debug_assert_eq!(capacity, buf.len());
        Ok(Self(ChunkVariant::PreEncoded(buf.into_boxed_slice())))
    }

    pub fn from_encoded(encoded: Vec<u8>) -> Self {
        Self(ChunkVariant::PreEncoded(encoded.into_boxed_slice()))
    }

    pub fn from_known_message<T: Message>(tag: u32, msg: T) -> EncodeResult<Self> {
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
}
