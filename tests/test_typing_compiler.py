import pytest

from betterproto.plugin.typing_compiler import (
    DirectImportTypingCompiler,
    NoTyping310TypingCompiler,
    TypingImportTypingCompiler,
)


def test_direct_import_typing_compiler():
    compiler = DirectImportTypingCompiler()
    assert compiler.imports() == {}
    assert compiler.optional("str") == "Optional[str]"
    assert compiler.imports() == {"typing": {"Optional"}}
    assert compiler.list("str") == "List[str]"
    assert compiler.imports() == {"typing": {"Optional", "List"}}
    assert compiler.dict("str", "int") == "Dict[str, int]"
    assert compiler.imports() == {"typing": {"Optional", "List", "Dict"}}
    assert compiler.union("str", "int") == "Union[str, int]"
    assert compiler.imports() == {"typing": {"Optional", "List", "Dict", "Union"}}
    assert compiler.iterable("str") == "Iterable[str]"
    assert compiler.imports() == {
        "typing": {"Optional", "List", "Dict", "Union", "Iterable"}
    }
    assert compiler.async_iterable("str") == "AsyncIterable[str]"
    assert compiler.imports() == {
        "typing": {"Optional", "List", "Dict", "Union", "Iterable", "AsyncIterable"}
    }
    assert compiler.async_iterator("str") == "AsyncIterator[str]"
    assert compiler.imports() == {
        "typing": {
            "Optional",
            "List",
            "Dict",
            "Union",
            "Iterable",
            "AsyncIterable",
            "AsyncIterator",
        }
    }


def test_typing_import_typing_compiler():
    compiler = TypingImportTypingCompiler()
    assert compiler.imports() == {}
    assert compiler.optional("str") == "typing.Optional[str]"
    assert compiler.imports() == {"typing": None}
    assert compiler.list("str") == "typing.List[str]"
    assert compiler.imports() == {"typing": None}
    assert compiler.dict("str", "int") == "typing.Dict[str, int]"
    assert compiler.imports() == {"typing": None}
    assert compiler.union("str", "int") == "typing.Union[str, int]"
    assert compiler.imports() == {"typing": None}
    assert compiler.iterable("str") == "typing.Iterable[str]"
    assert compiler.imports() == {"typing": None}
    assert compiler.async_iterable("str") == "typing.AsyncIterable[str]"
    assert compiler.imports() == {"typing": None}
    assert compiler.async_iterator("str") == "typing.AsyncIterator[str]"
    assert compiler.imports() == {"typing": None}


def test_no_typing_311_typing_compiler():
    compiler = NoTyping310TypingCompiler()
    assert compiler.imports() == {}
    assert compiler.optional("str") == '"str | None"'
    assert compiler.imports() == {}
    assert compiler.list("str") == '"list[str]"'
    assert compiler.imports() == {}
    assert compiler.dict("str", "int") == '"dict[str, int]"'
    assert compiler.imports() == {}
    assert compiler.union("str", "int") == '"str | int"'
    assert compiler.imports() == {}
    assert compiler.iterable("str") == '"Iterable[str]"'
    assert compiler.async_iterable("str") == '"AsyncIterable[str]"'
    assert compiler.async_iterator("str") == '"AsyncIterator[str]"'
    assert compiler.imports() == {
        "collections.abc": {"Iterable", "AsyncIterable", "AsyncIterator"}
    }
