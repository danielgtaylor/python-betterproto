import importlib
import pytest
import json

from generate import get_files

inputs = get_files(".bin")


@pytest.mark.parametrize("name,filename", inputs)
def test_sample(name: str, filename: str) -> None:
    imported = importlib.import_module(name)
    data_binary = open(filename, "rb").read()
    data_dict = json.loads(open(filename.replace(".bin", ".json")).read())
    t1 = imported.Test().parse(data_binary)
    t2 = imported.Test().from_dict(data_dict)
    print(t1)
    print(t2)
    assert t1 == t2
    assert bytes(t1) == data_binary
    assert bytes(t2) == data_binary
    assert t1.to_dict() == data_dict
    assert t2.to_dict() == data_dict
