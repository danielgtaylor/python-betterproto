import re

# Word delimiters and symbols that will not be preserved when re-casing.
# language=PythonRegExp
SYMBOLS = "[^a-zA-Z0-9]*"

# Optionally capitalized word.
# language=PythonRegExp
WORD = "[A-Z]*[a-z]*[0-9]*"

# Uppercase word, not followed by lowercase letters.
# language=PythonRegExp
WORD_UPPER = "[A-Z]+(?![a-z])[0-9]*"


def safe_snake_case(value: str) -> str:
    """Snake case a value taking into account Python keywords."""
    value = snake_case(value)
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


def snake_case(value: str):
    """
    Join words with an underscore into lowercase and remove symbols.
    """
    snake = re.sub(
        f"{SYMBOLS}({WORD_UPPER}|{WORD})", lambda groups: "_" + groups[1].lower(), value
    )
    return snake.strip("_")


def pascal_case(value: str):
    """
    Capitalize each word and remove symbols.
    """
    return re.sub(
        f"{SYMBOLS}({WORD_UPPER}|{WORD})", lambda groups: groups[1].capitalize(), value
    )


def camel_case(value: str):
    """
    Capitalize all words except first and remove symbols.
    """
    return capitalize_first(pascal_case(value))


def capitalize_first(value: str):
    return value[0:1].lower() + value[1:]
