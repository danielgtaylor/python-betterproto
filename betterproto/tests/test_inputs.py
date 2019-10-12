import importlib
import pytest
import json

from .generate import get_files, get_base

inputs = get_files(".bin")


@pytest.mark.parametrize("filename", inputs)
def test_sample(filename: str) -> None:
    module = get_base(filename).split("-")[0]
    imported = importlib.import_module(f"betterproto.tests.{module}")
    data_binary = open(filename, "rb").read()
    data_dict = json.loads(open(filename.replace(".bin", ".json")).read())
    t1 = imported.Test().parse(data_binary)
    t2 = imported.Test().from_dict(data_dict)
    print(t1)
    print(t2)

    # Equality should automagically work for dataclasses!
    assert t1 == t2

    # Generally this can't be relied on, but here we are aiming to match the
    # existing Python implementation and aren't doing anything tricky.
    # https://developers.google.com/protocol-buffers/docs/encoding#implications
    assert bytes(t1) == data_binary
    assert bytes(t2) == data_binary

    assert t1.to_dict() == data_dict
    assert t2.to_dict() == data_dict
