# Test cases that are expected to fail, e.g. unimplemented features or bug-fixes.
# Remove from list when fixed.
xfail = {
    "oneof_enum",  # 63
    "namespace_keywords",  # 70
    "namespace_builtin_types",  # 53
    "googletypes_struct",  # 9
    "googletypes_value",  # 9,
    "import_capitalized_package",
    "example",  # This is the example in the readme. Not a test.
}

services = {
    "googletypes_response",
    "googletypes_response_embedded",
    "service",
    "import_service_input_message",
    "googletypes_service_returns_empty",
    "googletypes_service_returns_googletype",
}
