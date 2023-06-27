import os
import re
from typing import (
    Dict,
    List,
    Set,
    Tuple,
    Type,
)

from ..casing import safe_snake_case
from ..lib.google import protobuf as google_protobuf
from .naming import pythonize_class_name


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


def parse_source_type_name(field_type_name: str) -> Tuple[str, str]:
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


def get_type_reference(
    *, package: str, imports: set, source_type: str, unwrap: bool = True
) -> str:
    """
    Return a Python type name for a proto type reference. Adds the import if
    necessary. Unwraps well known type if required.
    """
    if unwrap:
        if source_type in WRAPPER_TYPES:
            wrapped_type = type(WRAPPER_TYPES[source_type]().value)
            return f"Optional[{wrapped_type.__name__}]"

        if source_type == ".google.protobuf.Duration":
            return "timedelta"

        elif source_type == ".google.protobuf.Timestamp":
            return "datetime"

    source_package, source_type = parse_source_type_name(source_type)

    current_package: List[str] = package.split(".") if package else []
    py_package: List[str] = source_package.split(".") if source_package else []
    py_type: str = pythonize_class_name(source_type)

    compiling_google_protobuf = current_package == ["google", "protobuf"]
    importing_google_protobuf = py_package == ["google", "protobuf"]
    if importing_google_protobuf and not compiling_google_protobuf:
        py_package = ["betterproto", "lib"] + py_package

    if py_package[:1] == ["betterproto"]:
        return reference_absolute(imports, py_package, py_type)

    if py_package == current_package:
        return reference_sibling(py_type)

    if py_package[: len(current_package)] == current_package:
        return reference_descendent(current_package, imports, py_package, py_type)

    if current_package[: len(py_package)] == py_package:
        return reference_ancestor(current_package, imports, py_package, py_type)

    return reference_cousin(current_package, imports, py_package, py_type)


def reference_absolute(imports: Set[str], py_package: List[str], py_type: str) -> str:
    """
    Returns a reference to a python type located in the root, i.e. sys.path.
    """
    string_import = ".".join(py_package)
    string_alias = safe_snake_case(string_import)
    imports.add(f"import {string_import} as {string_alias}")
    return f'"{string_alias}.{py_type}"'


def reference_sibling(py_type: str) -> str:
    """
    Returns a reference to a python type within the same package as the current package.
    """
    return f'"{py_type}"'


def reference_descendent(
    current_package: List[str], imports: Set[str], py_package: List[str], py_type: str
) -> str:
    """
    Returns a reference to a python type in a package that is a descendent of the
    current package, and adds the required import that is aliased to avoid name
    conflicts.
    """
    importing_descendent = py_package[len(current_package) :]
    string_from = ".".join(importing_descendent[:-1])
    string_import = importing_descendent[-1]
    if string_from:
        string_alias = "_".join(importing_descendent)
        imports.add(f"from .{string_from} import {string_import} as {string_alias}")
        return f'"{string_alias}.{py_type}"'
    else:
        imports.add(f"from . import {string_import}")
        return f'"{string_import}.{py_type}"'


def reference_ancestor(
    current_package: List[str], imports: Set[str], py_package: List[str], py_type: str
) -> str:
    """
    Returns a reference to a python type in a package which is an ancestor to the
    current package, and adds the required import that is aliased (if possible) to avoid
    name conflicts.

    Adds trailing __ to avoid name mangling (python.org/dev/peps/pep-0008/#id34).
    """
    distance_up = len(current_package) - len(py_package)
    if py_package:
        string_import = py_package[-1]
        string_alias = f"_{'_' * distance_up}{string_import}__"
        string_from = f"..{'.' * distance_up}"
        imports.add(f"from {string_from} import {string_import} as {string_alias}")
        return f'"{string_alias}.{py_type}"'
    else:
        string_alias = f"{'_' * distance_up}{py_type}__"
        imports.add(f"from .{'.' * distance_up} import {py_type} as {string_alias}")
        return f'"{string_alias}"'


def reference_cousin(
    current_package: List[str], imports: Set[str], py_package: List[str], py_type: str
) -> str:
    """
    Returns a reference to a python type in a package that is not descendent, ancestor
    or sibling, and adds the required import that is aliased to avoid name conflicts.
    """
    shared_ancestry = os.path.commonprefix([current_package, py_package])  # type: ignore
    distance_up = len(current_package) - len(shared_ancestry)
    string_from = f".{'.' * distance_up}" + ".".join(
        py_package[len(shared_ancestry) : -1]
    )
    string_import = py_package[-1]
    # Add trailing __ to avoid name mangling (python.org/dev/peps/pep-0008/#id34)
    string_alias = (
        f"{'_' * distance_up}"
        + safe_snake_case(".".join(py_package[len(shared_ancestry) :]))
        + "__"
    )
    imports.add(f"from {string_from} import {string_import} as {string_alias}")
    return f'"{string_alias}.{py_type}"'
