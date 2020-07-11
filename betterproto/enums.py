from types import MappingProxyType
from typing import Any, Dict, Iterable, List, Mapping, NoReturn, Tuple

from .casing import camel_case, snake_case


def _is_descriptor(obj: Any) -> bool:
    return (
        hasattr(obj, "__get__") or hasattr(obj, "__set__") or hasattr(obj, "__delete__")
    )


class EnumMember:
    def __new__(cls, **kwargs):
        try:
            cls.name = kwargs['name']
            cls.value = kwargs['value']
        except KeyError:
            pass
        finally:
            return super().__new__(cls)

    def __repr__(self):
        return f"<{self._actual_enum_cls_.__name__}.{self.name}: {self.value!r}>"

    def __str__(self):
        return f"{self._actual_enum_cls_.__name__}.{self.name}"


class IntEnumMember(int, EnumMember):
    def __new__(cls, **kwargs) -> 'EnumMember':
        try:
            value = kwargs["value"]
            self = super().__new__(cls, value)
            self.name = kwargs["name"]
            self.value = value
            return self
        except KeyError:
            return super().__new__(cls)


class EnumMeta(type):
    def __new__(
        mcs, name: str, bases: Tuple[type, ...], attrs: Dict[str, Any]
    ) -> "EnumMeta":
        value_mapping: Dict[Any, EnumMember] = {}
        member_mapping: Dict[str, EnumMember] = {}
        member_names: List[str] = []

        value_cls = IntEnumMember if int in bases else EnumMember

        for key, value in tuple(attrs.items()):
            is_descriptor = _is_descriptor(value)
            if key[0] == "_" and not is_descriptor:
                continue

            # special case for classmethods to pass through
            if isinstance(value, classmethod):
                continue

            if is_descriptor:
                setattr(value_cls, key, value)
                del attrs[key]
                continue

            try:
                new_value = value_mapping[value]
            except KeyError:
                new_value = value_cls(name=key, value=value)
                value_mapping[value] = new_value
                member_names.append(key)

            member_mapping[key] = new_value
            attrs[key] = new_value

        attrs["_enum_value_map_"] = value_mapping
        attrs["_enum_member_map_"] = member_mapping
        attrs["_enum_member_names_"] = member_names
        enum_class = super().__new__(mcs, name, bases, attrs)
        value_cls._actual_enum_cls_ = enum_class
        for member in member_mapping.values():
            member._actual_enum_cls_ = enum_class
        return enum_class

    def __call__(cls, value: Any) -> "EnumMember":
        try:
            return cls._enum_value_map_[value]
        except (KeyError, TypeError):
            raise ValueError(f"{value!r} is not a valid {cls.__name__}")

    def __repr__(cls):
        return f"<enum {cls.__name__!r}>"

    def __iter__(cls) -> Iterable["EnumMember"]:
        return (cls._enum_member_map_[name] for name in cls._enum_member_names_)

    def __reversed__(cls) -> Iterable["EnumMember"]:
        return (
            cls._enum_member_map_[name] for name in reversed(cls._enum_member_names_)
        )

    def __len__(cls):
        return len(cls._enum_member_names_)

    def __getitem__(cls, key: Any) -> "EnumMember":
        return cls._enum_member_map_[key]

    def __setattr__(cls, name: str, value: Any) -> NoReturn:
        raise TypeError("Enums are immutable.")

    def __delattr__(cls, attr: Any) -> NoReturn:
        raise TypeError("Enums are immutable")

    def __instancecheck__(self, instance: Any):
        try:
            return instance._actual_enum_cls_ is self
        except AttributeError:
            return False

    @property
    def __members__(cls) -> Mapping[str, "EnumMemeber"]:
        return MappingProxyType(cls._enum_member_map_)


class Casing(metaclass=EnumMeta):
    """Casing constants for serialization."""

    CAMEL = camel_case
    SNAKE = snake_case


class Enum(int, metaclass=EnumMeta):
    """Protocol buffers enumeration base class. Acts like `enum.IntEnum`."""

    @classmethod
    def from_string(cls, name: str) -> EnumMember:
        """Return the value which corresponds to the string name."""
        try:
            return cls._enum_member_map_[name]
        except KeyError as e:
            raise ValueError(f"Unknown member {name!r} for enum {cls.__name__}") from e

    @classmethod
    def from_value(cls, value: int) -> EnumMember:
        """Return the value which corresponds to the integer value."""
        try:
            return cls._enum_value_map_[value]
        except KeyError as e:
            raise ValueError(f"Unknown value {name!r} for enum {cls.__name__}") from e
