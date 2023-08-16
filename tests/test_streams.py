from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Optional

import pytest

import betterproto
from tests.output_betterproto import (
    map,
    nested,
    oneof,
    repeated,
    repeatedpacked,
)


oneof_example = oneof.Test().from_dict(
    {"pitied": 1, "just_a_regular_field": 123456789, "bar_name": "Testing"}
)

nested_example = nested.Test().from_dict(
    {
        "nested": {"count": 1},
        "sibling": {"foo": 2},
        "sibling2": {"foo": 3},
        "msg": nested.TestMsg.THIS,
    }
)

repeated_example = repeated.Test().from_dict({"names": ["blah", "Blah2"]})

packed_example = repeatedpacked.Test().from_dict(
    {"counts": [1, 2, 3], "signed": [-1, 2, -3], "fixed": [1.2, -2.3, 3.4]}
)

map_example = map.Test().from_dict({"counts": {"blah": 1, "Blah2": 2}})

streams_path = Path("tests/streams/")


def test_load_varint_too_long():
    with BytesIO(
        b"\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x01"
    ) as stream, pytest.raises(ValueError):
        betterproto.load_varint(stream)

    with BytesIO(b"\x80\x80\x80\x80\x80\x80\x80\x80\x80\x01") as stream:
        # This should not raise a ValueError, as it is within 64 bits
        betterproto.load_varint(stream)


def test_load_varint_file():
    with open(streams_path / "message_dump_file_single.expected", "rb") as stream:
        assert betterproto.load_varint(stream) == (8, b"\x08")  # Single-byte varint
        stream.read(2)  # Skip until first multi-byte
        assert betterproto.load_varint(stream) == (
            123456789,
            b"\x95\x9A\xEF\x3A",
        )  # Multi-byte varint


def test_dump_varint_file(tmp_path):
    # Dump test varints to file
    with open(tmp_path / "dump_varint_file.out", "wb") as stream:
        betterproto.dump_varint(8, stream)  # Single-byte varint
        betterproto.dump_varint(123456789, stream)  # Multi-byte varint

    # Check that file contents are as expected
    with open(tmp_path / "dump_varint_file.out", "rb") as test_stream, open(
        streams_path / "message_dump_file_single.expected", "rb"
    ) as exp_stream:
        assert betterproto.load_varint(test_stream) == betterproto.load_varint(
            exp_stream
        )
        exp_stream.read(2)
        assert betterproto.load_varint(test_stream) == betterproto.load_varint(
            exp_stream
        )


def test_parse_fields():
    with open(streams_path / "message_dump_file_single.expected", "rb") as stream:
        parsed_bytes = betterproto.parse_fields(stream.read())

    with open(streams_path / "message_dump_file_single.expected", "rb") as stream:
        parsed_stream = betterproto.load_fields(stream)
        for field in parsed_bytes:
            assert field == next(parsed_stream)


def test_message_dump_file_single(tmp_path):
    # Write the message to the stream
    with open(tmp_path / "message_dump_file_single.out", "wb") as stream:
        oneof_example.dump(stream)

    # Check that the outputted file is exactly as expected
    with open(tmp_path / "message_dump_file_single.out", "rb") as test_stream, open(
        streams_path / "message_dump_file_single.expected", "rb"
    ) as exp_stream:
        assert test_stream.read() == exp_stream.read()


def test_message_dump_file_multiple(tmp_path):
    # Write the same Message twice and another, different message
    with open(tmp_path / "message_dump_file_multiple.out", "wb") as stream:
        oneof_example.dump(stream)
        oneof_example.dump(stream)
        nested_example.dump(stream)

    # Check that all three Messages were outputted to the file correctly
    with open(tmp_path / "message_dump_file_multiple.out", "rb") as test_stream, open(
        streams_path / "message_dump_file_multiple.expected", "rb"
    ) as exp_stream:
        assert test_stream.read() == exp_stream.read()


def test_message_len():
    assert len(oneof_example) == len(bytes(oneof_example))
    assert len(nested_example) == len(bytes(nested_example))


def test_message_load_file_single():
    with open(streams_path / "message_dump_file_single.expected", "rb") as stream:
        assert oneof.Test().load(stream) == oneof_example
        stream.seek(0)
        assert oneof.Test().load(stream, len(oneof_example)) == oneof_example


def test_message_load_file_multiple():
    with open(streams_path / "message_dump_file_multiple.expected", "rb") as stream:
        oneof_size = len(oneof_example)
        assert oneof.Test().load(stream, oneof_size) == oneof_example
        assert oneof.Test().load(stream, oneof_size) == oneof_example
        assert nested.Test().load(stream) == nested_example
        assert stream.read(1) == b""


def test_message_load_too_small():
    with open(
        streams_path / "message_dump_file_single.expected", "rb"
    ) as stream, pytest.raises(ValueError):
        oneof.Test().load(stream, len(oneof_example) - 1)


def test_message_too_large():
    with open(
        streams_path / "message_dump_file_single.expected", "rb"
    ) as stream, pytest.raises(ValueError):
        oneof.Test().load(stream, len(oneof_example) + 1)


def test_message_len_optional_field():
    @dataclass
    class Request(betterproto.Message):
        flag: Optional[bool] = betterproto.message_field(1, wraps=betterproto.TYPE_BOOL)

    assert len(Request()) == len(b"")
    assert len(Request(flag=True)) == len(b"\n\x02\x08\x01")
    assert len(Request(flag=False)) == len(b"\n\x00")


def test_message_len_repeated_field():
    assert len(repeated_example) == len(bytes(repeated_example))


def test_message_len_packed_field():
    assert len(packed_example) == len(bytes(packed_example))


def test_message_len_map_field():
    assert len(map_example) == len(bytes(map_example))


def test_message_len_empty_string():
    @dataclass
    class Empty(betterproto.Message):
        string: str = betterproto.string_field(1, "group")
        integer: int = betterproto.int32_field(2, "group")

    empty = Empty().from_dict({"string": ""})
    assert len(empty) == len(bytes(empty))


def test_calculate_varint_size_negative():
    single_byte = -1
    multi_byte = -10000000
    edge = -(1 << 63)
    beyond = -(1 << 63) - 1
    before = -(1 << 63) + 1

    assert (
        betterproto.size_varint(single_byte)
        == len(betterproto.encode_varint(single_byte))
        == 10
    )
    assert (
        betterproto.size_varint(multi_byte)
        == len(betterproto.encode_varint(multi_byte))
        == 10
    )
    assert betterproto.size_varint(edge) == len(betterproto.encode_varint(edge)) == 10
    assert (
        betterproto.size_varint(before) == len(betterproto.encode_varint(before)) == 10
    )

    with pytest.raises(ValueError):
        betterproto.size_varint(beyond)


def test_calculate_varint_size_positive():
    single_byte = 1
    multi_byte = 10000000

    assert betterproto.size_varint(single_byte) == len(
        betterproto.encode_varint(single_byte)
    )
    assert betterproto.size_varint(multi_byte) == len(
        betterproto.encode_varint(multi_byte)
    )


def test_dump_varint_negative(tmp_path):
    single_byte = -1
    multi_byte = -10000000
    edge = -(1 << 63)
    beyond = -(1 << 63) - 1
    before = -(1 << 63) + 1

    with open(tmp_path / "dump_varint_negative.out", "wb") as stream:
        betterproto.dump_varint(single_byte, stream)
        betterproto.dump_varint(multi_byte, stream)
        betterproto.dump_varint(edge, stream)
        betterproto.dump_varint(before, stream)

        with pytest.raises(ValueError):
            betterproto.dump_varint(beyond, stream)

    with open(streams_path / "dump_varint_negative.expected", "rb") as exp_stream, open(
        tmp_path / "dump_varint_negative.out", "rb"
    ) as test_stream:
        assert test_stream.read() == exp_stream.read()


def test_dump_varint_positive(tmp_path):
    single_byte = 1
    multi_byte = 10000000

    with open(tmp_path / "dump_varint_positive.out", "wb") as stream:
        betterproto.dump_varint(single_byte, stream)
        betterproto.dump_varint(multi_byte, stream)

    with open(tmp_path / "dump_varint_positive.out", "rb") as test_stream, open(
        streams_path / "dump_varint_positive.expected", "rb"
    ) as exp_stream:
        assert test_stream.read() == exp_stream.read()
