import re
from typing import Dict, List, Type

from betterproto import safe_snake_case
from betterproto.compile.naming import pythonize_class_name
from betterproto.lib.google import protobuf as google_protobuf

WRAPPER_TYPES: Dict[str, Type] = {
    ".google.protobuf.DoubleValue": google_protobuf.DoubleValue,
    ".google.protobuf.FloatValue": google_protobuf.FloatValue,
    ".google.protobuf.Int32Value": google_protobuf.Int32Value,
    ".google.protobuf.Int64Value": google_protobuf.Int64Value,
    ".google.protobuf.UInt32Value": google_protobuf.UInt32Value,
    ".google.protobuf.UInt64Value": google_protobuf.UInt64Value,
    ".google.protobuf.BoolValue": google_protobuf.BoolValue,
    ".google.protobuf.StringValue": google_protobuf.StringValue,
    ".google.protobuf.BytesValue": google_protobuf.BytesValue,
}


def parse_source_type_name(field_type_name):
    """
    Split full source type name into package and type name.
    E.g. 'root.package.Message' -> ('root.package', 'Message')
         'root.Message.SomeEnum' -> ('root', 'Message.SomeEnum')
    """
    package_match = re.match(r"^\.?([^A-Z]+)\.(.+)", field_type_name)
    if package_match:
        package = package_match.group(1)
        name = package_match.group(2)
    else:
        package = ""
        name = field_type_name.lstrip(".")
    return package, name


def get_ref_type(
    package: str, imports: set, source_type: str, unwrap: bool = True,
) -> str:
    """
    Return a Python type name for a proto type reference. Adds the import if
    necessary. Unwraps well known type if required.
    """
    is_wrapper = source_type in WRAPPER_TYPES

    if unwrap:
        if is_wrapper:
            wrapped_type = type(WRAPPER_TYPES[source_type]().value)
            return f"Optional[{wrapped_type.__name__}]"

        if source_type == ".google.protobuf.Duration":
            return "timedelta"

        if source_type == ".google.protobuf.Timestamp":
            return "datetime"

    source_package, source_type = parse_source_type_name(source_type)

    # Use precompiled classes for google.protobuf.* objects
    if source_package == "google.protobuf":
        string_import = f"betterproto.lib.{source_package}"
        py_type = source_type
        string_alias = safe_snake_case(string_import)
        imports.add(f"import {string_import} as {string_alias}")
        return f"{string_alias}.{py_type}"

    py_package: List[str] = source_package.split(".") if source_package else []
    py_type: str = pythonize_class_name(source_type)

    current_package: List[str] = package.split(".") if package else []

    # importing sibling
    """
    package = 
    name    = Foo

    package = foo
    name    = foo.Bar

    package = foo.bar
    name    = foo.bar.Baz
    """
    if py_package == current_package:
        return f'"{py_type}"'

    # importing child & descendent:
    """
    package = 
    name    = foo.Bar
    
    package = 
    name    = foo.bar.Baz
    """
    if py_package[0 : len(current_package)] == current_package:
        importing_descendent = py_package[len(current_package) :]
        string_from = ".".join(importing_descendent[0:-1])
        string_import = importing_descendent[-1]

        if string_from:
            string_alias = "_".join(importing_descendent)
            imports.add(f"from .{string_from} import {string_import} as {string_alias}")
            return f"{string_alias}.{py_type}"
        else:
            imports.add(f"from . import {string_import}")
            return f"{string_import}.{py_type}"

    # importing parent & ancestor
    """
    package = foo.bar
    name    = foo.Foo
    
    package = foo
    name    = Bar
    
    package = foo.bar.baz
    name    = Bar
    """
    if current_package[0 : len(py_package)] == py_package:
        distance_up = len(current_package) - len(py_package)
        imports.add(f"from .{'.' * distance_up} import {py_type}")
        return py_type

    # importing unrelated or cousin
    """
    package = foo.bar
    name    = baz.Foo

    package = foo.bar.baz
    name    = foo.example.Bar
    """
    shared_ancestory = [
        pair[0] for pair in zip(current_package, py_package) if pair[0] == pair[1]
    ]
    distance_up = len(current_package) - len(shared_ancestory)
    string_from = f".{'.' * distance_up}" + ".".join(
        py_package[len(shared_ancestory) : -1]
    )
    string_import = py_package[-1]
    alias = f"{'_' * distance_up}" + safe_snake_case(
        ".".join(py_package[len(shared_ancestory) :])
    )
    imports.add(f"from {string_from} import {string_import} as {alias}")
    return f"{alias}.{py_type}"
