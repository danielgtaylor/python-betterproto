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


def snake_case(value: str, strict: bool = True):
    """
    Join words with an underscore into lowercase and remove symbols.
    @param value: value to convert
    @param strict: force single underscores
    """

    def substitute_word(symbols, word, is_start):
        if not word:
            return ""
        if strict:
            delimiter_count = 0 if is_start else 1  # Single underscore if strict.
        elif is_start:
            delimiter_count = len(symbols)
        elif word.isupper() or word.islower():
            delimiter_count = max(1, len(symbols))  # Preserve all delimiters if not strict.
        else:
            delimiter_count = len(symbols) + 1  # Extra underscore for leading capital.

        return ("_" * delimiter_count) + word.lower()

    snake = re.sub(
        f"(^)?({SYMBOLS})({WORD_UPPER}|{WORD})",
        lambda groups: substitute_word(groups[2], groups[3], groups[1] is not None),
        value,
    )
    return snake


def pascal_case(value: str, strict: bool = True):
    """
    Capitalize each word and remove symbols.
    @param value: value to convert
    @param strict: output only alphanumeric characters
    """

    def substitute_word(symbols, word):
        if strict:
            return word.capitalize()  # Remove all delimiters

        if word.islower():
            delimiter_length = len(symbols[:-1])  # Lose one delimiter
        else:
            delimiter_length = len(symbols)  # Preserve all delimiters

        return ("_" * delimiter_length) + word.capitalize()

    return re.sub(
        f"({SYMBOLS})({WORD_UPPER}|{WORD})",
        lambda groups: substitute_word(groups[1], groups[2]),
        value,
    )


def camel_case(value: str, strict: bool = True):
    """
    Capitalize all words except first and remove symbols.
    """
    return lowercase_first(pascal_case(value, strict=strict))


def lowercase_first(value: str):
    return value[0:1].lower() + value[1:]
