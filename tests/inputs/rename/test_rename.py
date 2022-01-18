from dataclasses import fields

from tests.output_betterproto.rename import Renamed


def test_renamed_fields():
    assert {field.name for field in fields(Renamed)} == {
        "parse_",
        "serialized_on_wire_",
        "from_json_",
        "this",
    }
