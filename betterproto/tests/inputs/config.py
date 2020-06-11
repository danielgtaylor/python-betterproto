# Test cases that are expected to fail, e.g. unimplemented features or bug-fixes.
# Remove from list when fixed.
tests = {
    "import_root_sibling",  # 61
    "import_child_package_from_package",  # 58
    "import_root_package_from_child",  # 60
    "import_parent_package_from_child",  # 59
    "import_circular_dependency",  # failing because of other bugs now
    "import_packages_same_name",  # 25
    "oneof_enum",  # 63
    "casing_message_field_uppercase",  # 11
    "namespace_keywords",  # 70
    "namespace_builtin_types",  # 53
    "googletypes_struct",  # 9
    "googletypes_value",  # 9
}

services = {
    "googletypes_response",
    "googletypes_response_embedded",
    "service",
    "import_service_input_message",
    "googletypes_service_returns_empty",
    "googletypes_service_returns_googletype",
}
