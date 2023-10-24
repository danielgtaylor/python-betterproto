from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from shutil import which
from subprocess import run
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

len_oneof = len(oneof_example)

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

java = which("java")


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


def test_load_varint_cutoff():
    with open(streams_path / "load_varint_cutoff.in", "rb") as stream:
        with pytest.raises(EOFError):
            betterproto.load_varint(stream)

        stream.seek(1)
        with pytest.raises(EOFError):
            betterproto.load_varint(stream)


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


def test_message_dump_delimited(tmp_path):
    with open(tmp_path / "message_dump_delimited.out", "wb") as stream:
        oneof_example.dump(stream, betterproto.SIZE_DELIMITED)
        oneof_example.dump(stream, betterproto.SIZE_DELIMITED)
        nested_example.dump(stream, betterproto.SIZE_DELIMITED)

    with open(tmp_path / "message_dump_delimited.out", "rb") as test_stream, open(
        streams_path / "delimited_messages.in", "rb"
    ) as exp_stream:
        assert test_stream.read() == exp_stream.read()


def test_message_len():
    assert len_oneof == len(bytes(oneof_example))
    assert len(nested_example) == len(bytes(nested_example))


def test_message_load_file_single():
    with open(streams_path / "message_dump_file_single.expected", "rb") as stream:
        assert oneof.Test().load(stream) == oneof_example
        stream.seek(0)
        assert oneof.Test().load(stream, len_oneof) == oneof_example


def test_message_load_file_multiple():
    with open(streams_path / "message_dump_file_multiple.expected", "rb") as stream:
        oneof_size = len_oneof
        assert oneof.Test().load(stream, oneof_size) == oneof_example
        assert oneof.Test().load(stream, oneof_size) == oneof_example
        assert nested.Test().load(stream) == nested_example
        assert stream.read(1) == b""


def test_message_load_too_small():
    with open(
        streams_path / "message_dump_file_single.expected", "rb"
    ) as stream, pytest.raises(ValueError):
        oneof.Test().load(stream, len_oneof - 1)


def test_message_load_delimited():
    with open(streams_path / "delimited_messages.in", "rb") as stream:
        assert oneof.Test().load(stream, betterproto.SIZE_DELIMITED) == oneof_example
        assert oneof.Test().load(stream, betterproto.SIZE_DELIMITED) == oneof_example
        assert nested.Test().load(stream, betterproto.SIZE_DELIMITED) == nested_example
        assert stream.read(1) == b""


def test_message_load_too_large():
    with open(
        streams_path / "message_dump_file_single.expected", "rb"
    ) as stream, pytest.raises(ValueError):
        oneof.Test().load(stream, len_oneof + 1)


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


# Java compatibility tests


@pytest.fixture(scope="module")
def compile_jar():
    # Skip if not all required tools are present
    if java is None:
        pytest.skip("`java` command is absent and is required")
    mvn = which("mvn")
    if mvn is None:
        pytest.skip("Maven is absent and is required")

    # Compile the JAR
    proc_maven = run([mvn, "clean", "install", "-f", "tests/streams/java/pom.xml"])
    if proc_maven.returncode != 0:
        pytest.skip(
            "Maven compatibility-test.jar build failed (maybe Java version <11?)"
        )


jar = "tests/streams/java/target/compatibility-test.jar"


def run_jar(command: str, tmp_path):
    return run([java, "-jar", jar, command, tmp_path], check=True)


def run_java_single_varint(value: int, tmp_path) -> int:
    # Write single varint to file
    with open(tmp_path / "py_single_varint.out", "wb") as stream:
        betterproto.dump_varint(value, stream)

    # Have Java read this varint and write it back
    run_jar("single_varint", tmp_path)

    # Read single varint from Java output file
    with open(tmp_path / "java_single_varint.out", "rb") as stream:
        returned = betterproto.load_varint(stream)
        with pytest.raises(EOFError):
            betterproto.load_varint(stream)

    return returned


def test_single_varint(compile_jar, tmp_path):
    single_byte = (1, b"\x01")
    multi_byte = (123456789, b"\x95\x9A\xEF\x3A")

    # Write a single-byte varint to a file and have Java read it back
    returned = run_java_single_varint(single_byte[0], tmp_path)
    assert returned == single_byte

    # Same for a multi-byte varint
    returned = run_java_single_varint(multi_byte[0], tmp_path)
    assert returned == multi_byte


def test_multiple_varints(compile_jar, tmp_path):
    single_byte = (1, b"\x01")
    multi_byte = (123456789, b"\x95\x9A\xEF\x3A")
    over32 = (3000000000, b"\x80\xBC\xC1\x96\x0B")

    # Write two varints to the same file
    with open(tmp_path / "py_multiple_varints.out", "wb") as stream:
        betterproto.dump_varint(single_byte[0], stream)
        betterproto.dump_varint(multi_byte[0], stream)
        betterproto.dump_varint(over32[0], stream)

    # Have Java read these varints and write them back
    run_jar("multiple_varints", tmp_path)

    # Read varints from Java output file
    with open(tmp_path / "java_multiple_varints.out", "rb") as stream:
        returned_single = betterproto.load_varint(stream)
        returned_multi = betterproto.load_varint(stream)
        returned_over32 = betterproto.load_varint(stream)
        with pytest.raises(EOFError):
            betterproto.load_varint(stream)

    assert returned_single == single_byte
    assert returned_multi == multi_byte
    assert returned_over32 == over32


def test_single_message(compile_jar, tmp_path):
    # Write message to file
    with open(tmp_path / "py_single_message.out", "wb") as stream:
        oneof_example.dump(stream)

    # Have Java read and return the message
    run_jar("single_message", tmp_path)

    # Read and check the returned message
    with open(tmp_path / "java_single_message.out", "rb") as stream:
        returned = oneof.Test().load(stream, len(bytes(oneof_example)))
        assert stream.read() == b""

    assert returned == oneof_example


def test_multiple_messages(compile_jar, tmp_path):
    # Write delimited messages to file
    with open(tmp_path / "py_multiple_messages.out", "wb") as stream:
        oneof_example.dump(stream, betterproto.SIZE_DELIMITED)
        nested_example.dump(stream, betterproto.SIZE_DELIMITED)

    # Have Java read and return the messages
    run_jar("multiple_messages", tmp_path)

    # Read and check the returned messages
    with open(tmp_path / "java_multiple_messages.out", "rb") as stream:
        returned_oneof = oneof.Test().load(stream, betterproto.SIZE_DELIMITED)
        returned_nested = nested.Test().load(stream, betterproto.SIZE_DELIMITED)
        assert stream.read() == b""

    assert returned_oneof == oneof_example
    assert returned_nested == nested_example


def test_infinite_messages(compile_jar, tmp_path):
    num_messages = 5

    # Write delimited messages to file
    with open(tmp_path / "py_infinite_messages.out", "wb") as stream:
        for x in range(num_messages):
            oneof_example.dump(stream, betterproto.SIZE_DELIMITED)

    # Have Java read and return the messages
    run_jar("infinite_messages", tmp_path)

    # Read and check the returned messages
    messages = []
    with open(tmp_path / "java_infinite_messages.out", "rb") as stream:
        while True:
            try:
                messages.append(oneof.Test().load(stream, betterproto.SIZE_DELIMITED))
            except EOFError:
                break

    assert len(messages) == num_messages
