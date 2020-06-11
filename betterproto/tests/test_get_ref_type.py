import pytest

from ..compile.importing import get_ref_type


@pytest.mark.parametrize(
    ["google_type", "expected_name", "expected_import"],
    [
        (
            ".google.protobuf.Empty",
            "betterproto_lib_google_protobuf.Empty",
            "import betterproto.lib.google.protobuf as betterproto_lib_google_protobuf",
        ),
        (
            ".google.protobuf.Struct",
            "betterproto_lib_google_protobuf.Struct",
            "import betterproto.lib.google.protobuf as betterproto_lib_google_protobuf",
        ),
        (
            ".google.protobuf.ListValue",
            "betterproto_lib_google_protobuf.ListValue",
            "import betterproto.lib.google.protobuf as betterproto_lib_google_protobuf",
        ),
        (
            ".google.protobuf.Value",
            "betterproto_lib_google_protobuf.Value",
            "import betterproto.lib.google.protobuf as betterproto_lib_google_protobuf",
        ),
    ],
)
def test_import_google_wellknown_types_non_wrappers(
    google_type: str, expected_name: str, expected_import: str
):
    imports = set()
    name = get_ref_type(package="", imports=imports, type_name=google_type)

    assert name == expected_name
    assert imports.__contains__(expected_import)


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
def test_importing_google_wrappers_unwraps_them(google_type: str, expected_name: str):
    imports = set()
    name = get_ref_type(package="", imports=imports, type_name=google_type)

    assert name == expected_name
    assert imports == set()


@pytest.mark.parametrize(
    ["google_type", "expected_name"],
    [
        (".google.protobuf.DoubleValue", "betterproto_lib_google_protobuf.DoubleValue"),
        (".google.protobuf.FloatValue", "betterproto_lib_google_protobuf.FloatValue"),
        (".google.protobuf.Int32Value", "betterproto_lib_google_protobuf.Int32Value"),
        (".google.protobuf.Int64Value", "betterproto_lib_google_protobuf.Int64Value"),
        (".google.protobuf.UInt32Value", "betterproto_lib_google_protobuf.UInt32Value"),
        (".google.protobuf.UInt64Value", "betterproto_lib_google_protobuf.UInt64Value"),
        (".google.protobuf.BoolValue", "betterproto_lib_google_protobuf.BoolValue"),
        (".google.protobuf.StringValue", "betterproto_lib_google_protobuf.StringValue"),
        (".google.protobuf.BytesValue", "betterproto_lib_google_protobuf.BytesValue"),
    ],
)
def test_importing_google_wrappers_without_unwrapping(
    google_type: str, expected_name: str
):
    name = get_ref_type(package="", imports=set(), type_name=google_type, unwrap=False)

    assert name == expected_name
