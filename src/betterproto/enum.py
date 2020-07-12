from enum import EnumMeta as _EnumMeta, _is_dunder, _is_descriptor
from types import MappingProxyType
from typing import Any, Dict, Iterable, List, Mapping, NoReturn, Tuple

from .casing import camel_case, snake_case


class EnumMember:
    _actual_enum_cls_: "EnumMeta"
    name: str
    value: Any

    def __new__(cls, *, name: str, value: Any) -> "EnumMember":
        self = super().__new__(cls)
        self.name = name
        self.value = value
        return self

    def __repr__(self):
        return f"<{self._actual_enum_cls_.__name__}.{self.name}: {self.value!r}>"

    def __str__(self):
        return f"{self._actual_enum_cls_.__name__}.{self.name}"

    def __call__(self, *args: Tuple[Any, ...], **kwargs: Dict[str, Any]) -> Any:
        return self.value(*args, **kwargs)

    def __delattr__(self, item) -> NoReturn:
        raise ValueError("Enums are immutable.")

    def __setattr__(self, key, value) -> NoReturn:
        raise ValueError("Enums are immutable.")


class IntEnumMember(int, EnumMember):
    value: int

    def __new__(cls, *, name: str, value: int) -> "IntEnumMember":
        self = super().__new__(cls, value)
        self.name = name
        self.value = value
        return self


class EnumMeta(type):
    _enum_value_map_: Dict[Any, EnumMember]
    _enum_member_map_: Dict[str, EnumMember]
    _enum_member_names_: List[str]

    def __new__(
        mcs, name: str, bases: Tuple[type, ...], attrs: Dict[str, Any]
    ) -> "EnumMeta":
        value_mapping: Dict[Any, EnumMember] = {}
        member_mapping: Dict[str, EnumMember] = {}
        member_names: List[str] = []
        try:
            value_cls = IntEnumMember if IntEnum in bases else EnumMember
        except NameError:
            value_cls = EnumMember

        for key, value in tuple(attrs.items()):
            is_descriptor = _is_descriptor(value)
            if key[0] == "_" and not is_descriptor:
                continue

            if is_descriptor:
                if value not in (camel_case, snake_case):
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
        enum_class: "EnumMeta" = super().__new__(mcs, name, bases, attrs)
        for member in member_mapping.values():
            member._actual_enum_cls_ = enum_class
        return enum_class

    def __call__(cls, value: Any) -> "EnumMember":
        if isinstance(value, cls):
            return value
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

    def __getattr__(cls, name):
        if _is_dunder(name):
            raise AttributeError(name)
        try:
            return cls._enum_value_map_[name]
        except KeyError:
            raise AttributeError(name) from None

    def __setattr__(cls, name: str, value: Any) -> NoReturn:
        if name in cls._enum_member_map_:
            raise AttributeError("Cannot reassign members.")
        super().__setattr__(name, value)

    def __delattr__(cls, attr: Any) -> NoReturn:
        if attr in cls._enum_member_map_:
            raise AttributeError(f"{cls.__name__}: cannot delete Enum member.")
        super().__delattr__(attr)

    def __instancecheck__(self, instance: Any):
        try:
            return instance._actual_enum_cls_ is self
        except AttributeError:
            return False

    def __dir__(cls):
        return [
            "__class__",
            "__doc__",
            "__members__",
            "__module__",
        ] + cls._enum_member_names_

    def __contains__(cls, member: "EnumMeta"):
        if not isinstance(member, EnumMeta):
            raise TypeError(
                "unsupported operand type(s) for 'in':"
                f" '{member.__class__.__qualname__}' and '{cls.__class__.__qualname__}'"
            )
        return isinstance(member, EnumMember) and member.name in cls._enum_member_map_

    def __bool__(self):
        return True

    @property
    def __members__(cls) -> Mapping[str, "EnumMember"]:
        return MappingProxyType(cls._enum_member_map_)


class Enum(metaclass=EnumMeta):
    """Protocol buffers enumeration base base class. Acts like `enum.Enum`."""


class IntEnum(int, Enum):
    """Protocol buffers enumeration base class. Acts like `enum.IntEnum`."""


def patched_instance_check(self: _EnumMeta, instance: Any) -> bool:
    if isinstance(instance, (EnumMeta, EnumMember)):
        return True

    return type.__instancecheck__(self, instance)


_EnumMeta.__instancecheck__ = patched_instance_check  # fake it till you make it
