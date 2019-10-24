import stringcase


def safe_snake_case(value: str) -> str:
    """Snake case a value taking into account Python keywords."""
    value = stringcase.snakecase(value)
    if value in [
        "and",
        "as",
        "assert",
        "break",
        "class",
        "continue",
        "def",
        "del",
        "elif",
        "else",
        "except",
        "finally",
        "for",
        "from",
        "global",
        "if",
        "import",
        "in",
        "is",
        "lambda",
        "nonlocal",
        "not",
        "or",
        "pass",
        "raise",
        "return",
        "try",
        "while",
        "with",
        "yield",
    ]:
        # https://www.python.org/dev/peps/pep-0008/#descriptive-naming-styles
        value += "_"
    return value
