import keyword
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
    value = sanitize_name(value)
    return value


def snake_case(value: str, strict: bool = True) -> str:
    """
    Join words with an underscore into lowercase and remove symbols.

    Parameters
    -----------
    value: :class:`str`
        The value to convert.
    strict: :class:`bool`
        Whether or not to force single underscores.

    Returns
    --------
    :class:`str`
        The value in snake_case.
    """

    def substitute_word(symbols: str, word: str, is_start: bool) -> str:
        if not word:
            return ""
        if strict:
            delimiter_count = 0 if is_start else 1  # Single underscore if strict.
        elif is_start:
            delimiter_count = len(symbols)
        elif word.isupper() or word.islower():
            delimiter_count = max(
                1, len(symbols)
            )  # Preserve all delimiters if not strict.
        else:
            delimiter_count = len(symbols) + 1  # Extra underscore for leading capital.

        return ("_" * delimiter_count) + word.lower()

    snake = re.sub(
        f"(^)?({SYMBOLS})({WORD_UPPER}|{WORD})",
        lambda groups: substitute_word(groups[2], groups[3], groups[1] is not None),
        value,
    )
    return snake


def pascal_case(value: str, strict: bool = True) -> str:
    """
    Capitalize each word and remove symbols.

    Parameters
    -----------
    value: :class:`str`
        The value to convert.
    strict: :class:`bool`
        Whether or not to output only alphanumeric characters.

    Returns
    --------
    :class:`str`
        The value in PascalCase.
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


def camel_case(value: str, strict: bool = True) -> str:
    """
    Capitalize all words except first and remove symbols.

    Parameters
    -----------
    value: :class:`str`
        The value to convert.
    strict: :class:`bool`
        Whether or not to output only alphanumeric characters.

    Returns
    --------
    :class:`str`
        The value in camelCase.
    """
    return lowercase_first(pascal_case(value, strict=strict))


def lowercase_first(value: str) -> str:
    """
    Lower cases the first character of the value.

    Parameters
    ----------
    value: :class:`str`
        The value to lower case.

    Returns
    -------
    :class:`str`
        The lower cased string.
    """
    return value[0:1].lower() + value[1:]


def sanitize_name(value: str) -> str:
    # https://www.python.org/dev/peps/pep-0008/#descriptive-naming-styles
    return f"{value}_" if keyword.iskeyword(value) else value
