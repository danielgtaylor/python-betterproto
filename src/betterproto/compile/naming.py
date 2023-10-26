from betterproto import casing


def pythonize_class_name(name: str) -> str:
    return casing.pascal_case(name)


def pythonize_field_name(name: str) -> str:
    return casing.safe_snake_case(name)


def pythonize_method_name(name: str) -> str:
    return casing.safe_snake_case(name)


def pythonize_enum_member_name(name: str, enum_name: str) -> str:
    enum_name = casing.snake_case(enum_name).upper()
    find = name.find(enum_name)
    if find != -1:
        name = name[find + len(enum_name) :].strip("_")
    return casing.sanitize_name(name)
