# Test cases that are expected to fail, e.g. unimplemented features or bug-fixes.
# Remove from list when fixed.
tests = {
    "import_circular_dependency",
    "oneof_enum",  # 63
    "casing_message_field_uppercase",  # 11
    "namespace_keywords",  # 70
    "namespace_builtin_types",  # 53
    "googletypes_struct",  # 9
    "googletypes_value",  # 9
}


# Defines where the main package for this test resides.
# Needed to test relative package imports.
packages = {
    "import_root_package_from_child": ".child",
    "import_parent_package_from_child": ".parent.child",
    "repeatedmessage": ".repeatedmessage",
    "service": ".service",
}

services = {
    "googletypes_response",
    "googletypes_response_embedded",
    "service",
    "import_service_input_message",
    "googletypes_service_returns_empty",
    "googletypes_service_returns_googletype",
}
