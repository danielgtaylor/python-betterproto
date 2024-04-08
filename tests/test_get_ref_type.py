import pytest

from betterproto.compile.importing import (
    get_type_reference,
    parse_source_type_name,
)


@pytest.mark.parametrize(
    ["google_type", "expected_name", "expected_import"],
    [
        (
            ".google.protobuf.Empty",
            '"betterproto_lib_google_protobuf.Empty"',
            "import betterproto.lib.google.protobuf as betterproto_lib_google_protobuf",
        ),
        (
            ".google.protobuf.Struct",
            '"betterproto_lib_google_protobuf.Struct"',
            "import betterproto.lib.google.protobuf as betterproto_lib_google_protobuf",
        ),
        (
            ".google.protobuf.ListValue",
            '"betterproto_lib_google_protobuf.ListValue"',
            "import betterproto.lib.google.protobuf as betterproto_lib_google_protobuf",
        ),
        (
            ".google.protobuf.Value",
            '"betterproto_lib_google_protobuf.Value"',
            "import betterproto.lib.google.protobuf as betterproto_lib_google_protobuf",
        ),
    ],
)
def test_reference_google_wellknown_types_non_wrappers(
    google_type: str, expected_name: str, expected_import: str
):
    imports = set()
    name = get_type_reference(
        package="", imports=imports, source_type=google_type, pydantic=False
    )

    assert name == expected_name
    assert imports.__contains__(
        expected_import
    ), f"{expected_import} not found in {imports}"


@pytest.mark.parametrize(
    ["google_type", "expected_name"],
    [
        (".google.protobuf.DoubleValue", "Optional[float]"),
        (".google.protobuf.FloatValue", "Optional[float]"),
        (".google.protobuf.Int32Value", "Optional[int]"),
        (".google.protobuf.Int64Value", "Optional[int]"),
        (".google.protobuf.UInt32Value", "Optional[int]"),
        (".google.protobuf.UInt64Value", "Optional[int]"),
        (".google.protobuf.BoolValue", "Optional[bool]"),
        (".google.protobuf.StringValue", "Optional[str]"),
        (".google.protobuf.BytesValue", "Optional[bytes]"),
    ],
)
def test_referenceing_google_wrappers_unwraps_them(
    google_type: str, expected_name: str
):
    imports = set()
    name = get_type_reference(package="", imports=imports, source_type=google_type)

    assert name == expected_name
    assert imports == set()


@pytest.mark.parametrize(
    ["google_type", "expected_name"],
    [
        (
            ".google.protobuf.DoubleValue",
            '"betterproto_lib_google_protobuf.DoubleValue"',
        ),
        (".google.protobuf.FloatValue", '"betterproto_lib_google_protobuf.FloatValue"'),
        (".google.protobuf.Int32Value", '"betterproto_lib_google_protobuf.Int32Value"'),
        (".google.protobuf.Int64Value", '"betterproto_lib_google_protobuf.Int64Value"'),
        (
            ".google.protobuf.UInt32Value",
            '"betterproto_lib_google_protobuf.UInt32Value"',
        ),
        (
            ".google.protobuf.UInt64Value",
            '"betterproto_lib_google_protobuf.UInt64Value"',
        ),
        (".google.protobuf.BoolValue", '"betterproto_lib_google_protobuf.BoolValue"'),
        (
            ".google.protobuf.StringValue",
            '"betterproto_lib_google_protobuf.StringValue"',
        ),
        (".google.protobuf.BytesValue", '"betterproto_lib_google_protobuf.BytesValue"'),
    ],
)
def test_referenceing_google_wrappers_without_unwrapping(
    google_type: str, expected_name: str
):
    name = get_type_reference(
        package="", imports=set(), source_type=google_type, unwrap=False
    )

    assert name == expected_name


def test_reference_child_package_from_package():
    imports = set()
    name = get_type_reference(
        package="package", imports=imports, source_type="package.child.Message"
    )

    assert imports == {"from . import child"}
    assert name == '"child.Message"'


def test_reference_child_package_from_root():
    imports = set()
    name = get_type_reference(package="", imports=imports, source_type="child.Message")

    assert imports == {"from . import child"}
    assert name == '"child.Message"'


def test_reference_camel_cased():
    imports = set()
    name = get_type_reference(
        package="", imports=imports, source_type="child_package.example_message"
    )

    assert imports == {"from . import child_package"}
    assert name == '"child_package.ExampleMessage"'


def test_reference_nested_child_from_root():
    imports = set()
    name = get_type_reference(
        package="", imports=imports, source_type="nested.child.Message"
    )

    assert imports == {"from .nested import child as nested_child"}
    assert name == '"nested_child.Message"'


def test_reference_deeply_nested_child_from_root():
    imports = set()
    name = get_type_reference(
        package="", imports=imports, source_type="deeply.nested.child.Message"
    )

    assert imports == {"from .deeply.nested import child as deeply_nested_child"}
    assert name == '"deeply_nested_child.Message"'


def test_reference_deeply_nested_child_from_package():
    imports = set()
    name = get_type_reference(
        package="package",
        imports=imports,
        source_type="package.deeply.nested.child.Message",
    )

    assert imports == {"from .deeply.nested import child as deeply_nested_child"}
    assert name == '"deeply_nested_child.Message"'


def test_reference_root_sibling():
    imports = set()
    name = get_type_reference(package="", imports=imports, source_type="Message")

    assert imports == set()
    assert name == '"Message"'


def test_reference_nested_siblings():
    imports = set()
    name = get_type_reference(package="foo", imports=imports, source_type="foo.Message")

    assert imports == set()
    assert name == '"Message"'


def test_reference_deeply_nested_siblings():
    imports = set()
    name = get_type_reference(
        package="foo.bar", imports=imports, source_type="foo.bar.Message"
    )

    assert imports == set()
    assert name == '"Message"'


def test_reference_parent_package_from_child():
    imports = set()
    name = get_type_reference(
        package="package.child", imports=imports, source_type="package.Message"
    )

    assert imports == {"from ... import package as __package__"}
    assert name == '"__package__.Message"'


def test_reference_parent_package_from_deeply_nested_child():
    imports = set()
    name = get_type_reference(
        package="package.deeply.nested.child",
        imports=imports,
        source_type="package.deeply.nested.Message",
    )

    assert imports == {"from ... import nested as __nested__"}
    assert name == '"__nested__.Message"'


def test_reference_ancestor_package_from_nested_child():
    imports = set()
    name = get_type_reference(
        package="package.ancestor.nested.child",
        imports=imports,
        source_type="package.ancestor.Message",
    )

    assert imports == {"from .... import ancestor as ___ancestor__"}
    assert name == '"___ancestor__.Message"'


def test_reference_root_package_from_child():
    imports = set()
    name = get_type_reference(
        package="package.child", imports=imports, source_type="Message"
    )

    assert imports == {"from ... import Message as __Message__"}
    assert name == '"__Message__"'


def test_reference_root_package_from_deeply_nested_child():
    imports = set()
    name = get_type_reference(
        package="package.deeply.nested.child", imports=imports, source_type="Message"
    )

    assert imports == {"from ..... import Message as ____Message__"}
    assert name == '"____Message__"'


def test_reference_unrelated_package():
    imports = set()
    name = get_type_reference(package="a", imports=imports, source_type="p.Message")

    assert imports == {"from .. import p as _p__"}
    assert name == '"_p__.Message"'


def test_reference_unrelated_nested_package():
    imports = set()
    name = get_type_reference(package="a.b", imports=imports, source_type="p.q.Message")

    assert imports == {"from ...p import q as __p_q__"}
    assert name == '"__p_q__.Message"'


def test_reference_unrelated_deeply_nested_package():
    imports = set()
    name = get_type_reference(
        package="a.b.c.d", imports=imports, source_type="p.q.r.s.Message"
    )

    assert imports == {"from .....p.q.r import s as ____p_q_r_s__"}
    assert name == '"____p_q_r_s__.Message"'


def test_reference_cousin_package():
    imports = set()
    name = get_type_reference(package="a.x", imports=imports, source_type="a.y.Message")

    assert imports == {"from .. import y as _y__"}
    assert name == '"_y__.Message"'


def test_reference_cousin_package_different_name():
    imports = set()
    name = get_type_reference(
        package="test.package1", imports=imports, source_type="cousin.package2.Message"
    )

    assert imports == {"from ...cousin import package2 as __cousin_package2__"}
    assert name == '"__cousin_package2__.Message"'


def test_reference_cousin_package_same_name():
    imports = set()
    name = get_type_reference(
        package="test.package", imports=imports, source_type="cousin.package.Message"
    )

    assert imports == {"from ...cousin import package as __cousin_package__"}
    assert name == '"__cousin_package__.Message"'


def test_reference_far_cousin_package():
    imports = set()
    name = get_type_reference(
        package="a.x.y", imports=imports, source_type="a.b.c.Message"
    )

    assert imports == {"from ...b import c as __b_c__"}
    assert name == '"__b_c__.Message"'


def test_reference_far_far_cousin_package():
    imports = set()
    name = get_type_reference(
        package="a.x.y.z", imports=imports, source_type="a.b.c.d.Message"
    )

    assert imports == {"from ....b.c import d as ___b_c_d__"}
    assert name == '"___b_c_d__.Message"'


@pytest.mark.parametrize(
    ["full_name", "expected_output"],
    [
        ("package.SomeMessage.NestedType", ("package", "SomeMessage.NestedType")),
        (".package.SomeMessage.NestedType", ("package", "SomeMessage.NestedType")),
        (".service.ExampleRequest", ("service", "ExampleRequest")),
        (".package.lower_case_message", ("package", "lower_case_message")),
    ],
)
def test_parse_field_type_name(full_name, expected_output):
    assert parse_source_type_name(full_name) == expected_output
