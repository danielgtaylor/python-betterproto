from dataclasses import dataclass
from pathlib import Path
from typing import Union


class CLIError(Exception):
    """The base class for all exceptions when compiling a file"""


class CompilerError(CLIError):
    ...


class ProtobufSyntaxError(SyntaxError, CompilerError):
    """
    Attributes
    ----------
    msg: :class:`str`
        The message given by protoc e.g. "Expected top-level statement (e.g. "message")."
    file: :class:`.Path`
        The file that had the syntax error.
    lineno: :class:`int`
        The line number on which the syntax error occurs.
    offset: :class:`int`
        The offset along the :attr:`lineno` that the syntax error occurs.
    """

    def __init__(self, msg: str, file: Path, lineno: int, offset: int):
        text = file.read_text().splitlines()[lineno - 1]
        super().__init__(msg, (str(file), lineno, offset, text))
        self.file = file


@dataclass
class UnusedImport(CLIError, ImportWarning):
    """The warning emitted when an unused import is detected by protoc.

    Attributes
    ----------
    msg: :class:`str`
        The message given by protoc e.g. "Expected top-level statement (e.g. "message")."
    file: :class:`.Path`
        The file that had the warning issued for.
    used_import: :class:`.Path`
        The unused import file.
    """

    msg: str
    file: Path
    unused_import: Union[Path, str]

    def __str__(self):
        return f"Import {self.unused_import} is unused in {self.file}"
