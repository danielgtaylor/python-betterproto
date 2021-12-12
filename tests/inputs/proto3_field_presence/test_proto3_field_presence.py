import json

from tests.output_betterproto.proto3_field_presence import Test, InnerTest, TestEnum


def test_null_fields_json():
    """Ensure that using "null" in JSON is equivalent to not specifying a
    field, for fields with explicit presence"""

    def test_json(ref_json: str, obj_json: str) -> None:
        """`ref_json` and `obj_json` are JSON strings describing a `Test` object.
        Test that deserializing both leads to the same object, and that
        `ref_json` is the normalized format."""
        ref_obj = Test().from_json(ref_json)
        obj = Test().from_json(obj_json)

        assert obj == ref_obj
        assert json.loads(obj.to_json(0)) == json.loads(ref_json)

    test_json("{}", '{ "test1": null, "test2": null, "test3": null }')
    test_json("{}", '{ "test4": null, "test5": null, "test6": null }')
    test_json("{}", '{ "test7": null, "test8": null }')
    test_json('{ "test5": {} }', '{ "test3": null, "test5": {} }')

    # Make sure that if include_default_values is set, None values are
    # exported.
    obj = Test()
    assert obj.to_dict() == {}
    assert obj.to_dict(include_default_values=True) == {
        "test1": None,
        "test2": None,
        "test3": None,
        "test4": None,
        "test5": None,
        "test6": None,
        "test7": None,
        "test8": None,
    }
