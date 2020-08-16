from ...betterproto import casing


def pythonize_class_name(name):
    return casing.pascal_case(name)


def pythonize_field_name(name: str):
    return casing.safe_snake_case(name)


def pythonize_method_name(name: str):
    return casing.safe_snake_case(name)
