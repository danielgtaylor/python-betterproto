# Test cases that are expected to fail, e.g. unimplemented features or bug-fixes.
# Remove from list when fixed.
xfail = {
    "namespace_keywords",  # 70
    "googletypes_struct",  # 9
    "googletypes_value",  # 9
    "import_capitalized_package",
    "example",  # This is the example in the readme. Not a test.
}

services = {
    "googletypes_request",
    "googletypes_response",
    "googletypes_response_embedded",
    "service",
    "service_separate_packages",
    "import_service_input_message",
    "googletypes_service_returns_empty",
    "googletypes_service_returns_googletype",
    "example_service",
    "empty_service",
}


# Indicate json sample messages to skip when testing that json (de)serialization
# is symmetrical becuase some cases legitimately are not symmetrical.
# Each key references the name of the test scenario and the values in the tuple
# Are the names of the json files.
non_symmetrical_json = {"empty_repeated": ("empty_repeated",)}
