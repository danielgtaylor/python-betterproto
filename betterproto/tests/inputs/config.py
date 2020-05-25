# Test cases that are expected to fail, e.g. unimplemented features or bug-fixes.
# Remove from list when fixed.
tests = {
    "import_root_sibling",
    "import_child_package_from_package",
    "import_root_package_from_child",
    "import_parent_package_from_child",
    "import_circular_dependency",
    "import_packages_same_name",
    "oneof_enum",
    "googletypes_service_returns_empty",
}

services = {
    "googletypes_response",
    "googletypes_response_embedded",
    "service",
    "import_service_input_message",
    "import_service_input_message_dependency",
    "googletypes_service_returns_empty"
}
