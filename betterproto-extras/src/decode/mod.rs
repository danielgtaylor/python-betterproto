mod custom_message;
mod error;
mod field;
mod map_entry;
mod value;

use self::custom_message::CustomMessageBuilder;
pub use self::error::{DecodeError, DecodeResult};
use crate::betterproto_interop::BetterprotoMessage;
use prost::{
    bytes::Buf,
    encoding::{check_wire_type, decode_varint, WireType},
};

pub fn merge_into_message(msg: BetterprotoMessage, buf: &mut impl Buf) -> DecodeResult<()> {
    let py = msg.py();
    let cls = msg.class();
    let mut builder = CustomMessageBuilder::new(py, cls.descriptor(py)?);
    while buf.has_remaining() {
        builder.parse_next_field(buf)?;
    }
    builder.merge_into(msg)?;
    Ok(())
}

trait MessageBuilder {
    fn parse_next_field(&mut self, buf: &mut impl Buf) -> DecodeResult<()>;

    fn parse_next_length_delimited(
        &mut self,
        wire_type: WireType,
        buf: &mut impl Buf,
    ) -> DecodeResult<()> {
        check_wire_type(WireType::LengthDelimited, wire_type)?;
        let len = decode_varint(buf)?;
        let remaining = buf.remaining();
        if len > remaining as u64 {
            return Err(DecodeError::InvalidData);
        }

        let limit = remaining - len as usize;
        while buf.remaining() > limit {
            self.parse_next_field(buf)?;
        }

        if buf.remaining() != limit {
            return Err(DecodeError::InvalidData);
        }

        Ok(())
    }
}
