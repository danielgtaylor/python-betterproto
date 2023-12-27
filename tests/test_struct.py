import json

from betterproto.lib.google.protobuf import Struct


def test_struct_roundtrip():
    data = {
        "foo": "bar",
        "baz": None,
        "quux": 123,
        "zap": [1, {"two": 3}, "four"],
    }
    data_json = json.dumps(data)

    struct_from_dict = Struct().from_dict(data)
    assert struct_from_dict.fields == data
    assert struct_from_dict.to_dict() == data
    assert struct_from_dict.to_json() == data_json

    struct_from_json = Struct().from_json(data_json)
    assert struct_from_json.fields == data
    assert struct_from_json.to_dict() == data
    assert struct_from_json == struct_from_dict
    assert struct_from_json.to_json() == data_json
