from typing import Dict, Type

import stringcase

from betterproto import safe_snake_case
from betterproto.lib.google import protobuf as google_protobuf

WRAPPER_TYPES: Dict[str, Type] = {
    "google.protobuf.DoubleValue": google_protobuf.DoubleValue,
    "google.protobuf.FloatValue": google_protobuf.FloatValue,
    "google.protobuf.Int32Value": google_protobuf.Int32Value,
    "google.protobuf.Int64Value": google_protobuf.Int64Value,
    "google.protobuf.UInt32Value": google_protobuf.UInt32Value,
    "google.protobuf.UInt64Value": google_protobuf.UInt64Value,
    "google.protobuf.BoolValue": google_protobuf.BoolValue,
    "google.protobuf.StringValue": google_protobuf.StringValue,
    "google.protobuf.BytesValue": google_protobuf.BytesValue,
}


def get_ref_type(
    package: str, imports: set, type_name: str, unwrap: bool = True
) -> str:
    """
    Return a Python type name for a proto type reference. Adds the import if
    necessary. Unwraps well known type if required.
    """
    # If the package name is a blank string, then this should still work
    # because by convention packages are lowercase and message/enum types are
    # pascal-cased. May require refactoring in the future.
    type_name = type_name.lstrip(".")

    is_wrapper = type_name in WRAPPER_TYPES

    if unwrap:
        if is_wrapper:
            wrapped_type = type(WRAPPER_TYPES[type_name]().value)
            return f"Optional[{wrapped_type.__name__}]"

        if type_name == "google.protobuf.Duration":
            return "timedelta"

        if type_name == "google.protobuf.Timestamp":
            return "datetime"

    if type_name.startswith(package):
        parts = type_name.lstrip(package).lstrip(".").split(".")
        if len(parts) == 1 or (len(parts) > 1 and parts[0][0] == parts[0][0].upper()):
            # This is the current package, which has nested types flattened.
            # foo.bar_thing => FooBarThing
            cased = [stringcase.pascalcase(part) for part in parts]
            type_name = f'"{"".join(cased)}"'

    # Use precompiled classes for google.protobuf.* objects
    if type_name.startswith("google.protobuf.") and type_name.count(".") == 2:
        type_name = type_name.rsplit(".", maxsplit=1)[1]
        import_package = "betterproto.lib.google.protobuf"
        import_alias = safe_snake_case(import_package)
        imports.add(f"import {import_package} as {import_alias}")
        return f"{import_alias}.{type_name}"

    if "." in type_name:
        # This is imported from another package. No need
        # to use a forward ref and we need to add the import.
        parts = type_name.split(".")
        parts[-1] = stringcase.pascalcase(parts[-1])
        imports.add(f"from .{'.'.join(parts[:-2])} import {parts[-2]}")
        type_name = f"{parts[-2]}.{parts[-1]}"

    return type_name
