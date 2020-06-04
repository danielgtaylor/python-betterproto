from typing import Dict, List, Type

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


    # Use precompiled classes for google.protobuf.* objects
    if type_name.startswith("google.protobuf.") and type_name.count(".") == 2:
        type_name = type_name.rsplit(".", maxsplit=1)[1]
        import_package = "betterproto.lib.google.protobuf"
        import_alias = safe_snake_case(import_package)
        imports.add(f"import {import_package} as {import_alias}")
        return f"{import_alias}.{type_name}"

    importing_package: List[str] = type_name.split('.')
    importing_type: str = stringcase.pascalcase(importing_package.pop())
    current_package: List[str] = package.split('.') if package else []

    # importing sibling
    '''
    package = 
    name    = Foo

    package = foo
    name    = foo.Bar

    package = foo.bar
    name    = foo.bar.Baz
    '''
    if importing_package == current_package:
        imports.add(f"from . import {importing_type}")
        return importing_type

    # importing child & descendent:
    '''
    package = 
    name    = foo.Bar
    
    package = 
    name    = foo.bar.Baz
    '''
    if importing_package[0:len(current_package)] == current_package:
        relative_importing_package = '.'.join(importing_package[len(current_package):])
        imports.add(f"from . import {relative_importing_package}")
        return f"{relative_importing_package}.{importing_type}"

    # importing parent & ancestor
    '''
    package = foo.bar
    name    = foo.Foo
    
    package = foo
    name    = Bar
    
    package = foo.bar.baz
    name    = Bar
    '''

    # importing unrelated or cousin
    '''
    package = foo.bar
    name    = baz.Foo

    package = foo.bar.baz
    name    = foo.example.Bar
    '''

    return None
    # return type_name
