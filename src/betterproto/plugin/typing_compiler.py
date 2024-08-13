import abc
from collections import defaultdict
from dataclasses import (
    dataclass,
    field,
)
from typing import (
    Dict,
    Iterator,
    Optional,
    Set,
)


class TypingCompiler(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def optional(self, type: str) -> str:
        raise NotImplementedError()

    @abc.abstractmethod
    def list(self, type: str) -> str:
        raise NotImplementedError()

    @abc.abstractmethod
    def dict(self, key: str, value: str) -> str:
        raise NotImplementedError()

    @abc.abstractmethod
    def union(self, *types: str) -> str:
        raise NotImplementedError()

    @abc.abstractmethod
    def iterable(self, type: str) -> str:
        raise NotImplementedError()

    @abc.abstractmethod
    def async_iterable(self, type: str) -> str:
        raise NotImplementedError()

    @abc.abstractmethod
    def async_iterator(self, type: str) -> str:
        raise NotImplementedError()

    @abc.abstractmethod
    def imports(self) -> Dict[str, Optional[Set[str]]]:
        """
        Returns either the direct import as a key with none as value, or a set of
        values to import from the key.
        """
        raise NotImplementedError()

    def import_lines(self) -> Iterator:
        imports = self.imports()
        for key, value in imports.items():
            if value is None:
                yield f"import {key}"
            else:
                yield f"from {key} import ("
                for v in sorted(value):
                    yield f"    {v},"
                yield ")"


@dataclass
class DirectImportTypingCompiler(TypingCompiler):
    _imports: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))

    def optional(self, type: str) -> str:
        self._imports["typing"].add("Optional")
        return f"Optional[{type}]"

    def list(self, type: str) -> str:
        self._imports["typing"].add("List")
        return f"List[{type}]"

    def dict(self, key: str, value: str) -> str:
        self._imports["typing"].add("Dict")
        return f"Dict[{key}, {value}]"

    def union(self, *types: str) -> str:
        self._imports["typing"].add("Union")
        return f"Union[{', '.join(types)}]"

    def iterable(self, type: str) -> str:
        self._imports["typing"].add("Iterable")
        return f"Iterable[{type}]"

    def async_iterable(self, type: str) -> str:
        self._imports["typing"].add("AsyncIterable")
        return f"AsyncIterable[{type}]"

    def async_iterator(self, type: str) -> str:
        self._imports["typing"].add("AsyncIterator")
        return f"AsyncIterator[{type}]"

    def imports(self) -> Dict[str, Optional[Set[str]]]:
        return {k: v if v else None for k, v in self._imports.items()}


@dataclass
class TypingImportTypingCompiler(TypingCompiler):
    _imported: bool = False

    def optional(self, type: str) -> str:
        self._imported = True
        return f"typing.Optional[{type}]"

    def list(self, type: str) -> str:
        self._imported = True
        return f"typing.List[{type}]"

    def dict(self, key: str, value: str) -> str:
        self._imported = True
        return f"typing.Dict[{key}, {value}]"

    def union(self, *types: str) -> str:
        self._imported = True
        return f"typing.Union[{', '.join(types)}]"

    def iterable(self, type: str) -> str:
        self._imported = True
        return f"typing.Iterable[{type}]"

    def async_iterable(self, type: str) -> str:
        self._imported = True
        return f"typing.AsyncIterable[{type}]"

    def async_iterator(self, type: str) -> str:
        self._imported = True
        return f"typing.AsyncIterator[{type}]"

    def imports(self) -> Dict[str, Optional[Set[str]]]:
        if self._imported:
            return {"typing": None}
        return {}


@dataclass
class NoTyping310TypingCompiler(TypingCompiler):
    _imports: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))

    @staticmethod
    def _fmt(type: str) -> str:  # for now this is necessary till 3.14
        if type.startswith('"'):
            return type[1:-1]
        return type

    def optional(self, type: str) -> str:
        return f'"{self._fmt(type)} | None"'

    def list(self, type: str) -> str:
        return f'"list[{self._fmt(type)}]"'

    def dict(self, key: str, value: str) -> str:
        return f'"dict[{key}, {self._fmt(value)}]"'

    def union(self, *types: str) -> str:
        return f'"{" | ".join(map(self._fmt, types))}"'

    def iterable(self, type: str) -> str:
        self._imports["collections.abc"].add("Iterable")
        return f'"Iterable[{type}]"'

    def async_iterable(self, type: str) -> str:
        self._imports["collections.abc"].add("AsyncIterable")
        return f'"AsyncIterable[{type}]"'

    def async_iterator(self, type: str) -> str:
        self._imports["collections.abc"].add("AsyncIterator")
        return f'"AsyncIterator[{type}]"'

    def imports(self) -> Dict[str, Optional[Set[str]]]:
        return {k: v if v else None for k, v in self._imports.items()}
