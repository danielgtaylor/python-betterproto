from __future__ import annotations

from enum import (
    EnumMeta,
    IntEnum,
)
from types import MappingProxyType
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Optional,
    Tuple,
)


if TYPE_CHECKING:
    from collections.abc import (
        Generator,
        Mapping,
    )

    from typing_extensions import (
        Never,
        Self,
    )


def _is_descriptor(obj: object) -> bool:
    return (
        hasattr(obj, "__get__") or hasattr(obj, "__set__") or hasattr(obj, "__delete__")
    )


class EnumType(EnumMeta if TYPE_CHECKING else type):
    _value_map_: Mapping[int, Enum]
    _member_map_: Mapping[str, Enum]
    _proto_names_: Dict[str, str]  # Maps Python name -> original proto name

    def __new__(
        mcs, name: str, bases: Tuple[type, ...], namespace: Dict[str, Any]
    ) -> Self:
        value_map = {}
        member_map = {}
        proto_names = namespace.pop("_proto_names_", {})

        new_mcs = type(
            f"{name}Type",
            tuple(
                dict.fromkeys(
                    [base.__class__ for base in bases if base.__class__ is not type]
                    + [EnumType, type]
                )
            ),  # reorder the bases so EnumType and type are last to avoid conflicts
            {
                "_value_map_": value_map,
                "_member_map_": member_map,
                "_proto_names_": proto_names,
            },
        )

        members = {
            name: value
            for name, value in namespace.items()
            if not _is_descriptor(value) and not name.startswith("__")
        }

        cls = type.__new__(
            new_mcs,
            name,
            bases,
            {key: value for key, value in namespace.items() if key not in members},
        )
        # this allows us to disallow member access from other members as
        # members become proper class variables

        for name, value in members.items():
            member = value_map.get(value)
            if member is None:
                proto_name = proto_names.get(name, name)
                member = cls.__new__(cls, name=name, value=value, proto_name=proto_name)  # type: ignore
                value_map[value] = member
            member_map[name] = member
            type.__setattr__(new_mcs, name, member)

        return cls

    if not TYPE_CHECKING:

        def __call__(cls, value: int) -> Enum:
            try:
                return cls._value_map_[value]
            except (KeyError, TypeError):
                raise ValueError(f"{value!r} is not a valid {cls.__name__}") from None

        def __iter__(cls) -> Generator[Enum, None, None]:
            yield from cls._member_map_.values()

        def __reversed__(cls) -> Generator[Enum, None, None]:
            yield from reversed(cls._member_map_.values())

        def __getitem__(cls, key: str) -> Enum:
            return cls._member_map_[key]

        @property
        def __members__(cls) -> MappingProxyType[str, Enum]:
            return MappingProxyType(cls._member_map_)

    def __repr__(cls) -> str:
        return f"<enum {cls.__name__!r}>"

    def __len__(cls) -> int:
        return len(cls._member_map_)

    def __setattr__(cls, name: str, value: Any) -> Never:
        raise AttributeError(f"{cls.__name__}: cannot reassign Enum members.")

    def __delattr__(cls, name: str) -> Never:
        raise AttributeError(f"{cls.__name__}: cannot delete Enum members.")

    def __contains__(cls, member: object) -> bool:
        return isinstance(member, cls) and member.name in cls._member_map_


class Enum(IntEnum if TYPE_CHECKING else int, metaclass=EnumType):
    """
    The base class for protobuf enumerations, all generated enumerations will
    inherit from this. Emulates `enum.IntEnum`.
    """

    name: Optional[str]
    value: int
    proto_name: Optional[str]

    if not TYPE_CHECKING:

        def __new__(
            cls, *, name: Optional[str], value: int, proto_name: Optional[str] = None
        ) -> Self:
            self = super().__new__(cls, value)
            super().__setattr__(self, "name", name)
            super().__setattr__(self, "value", value)
            # proto_name is the original name from the .proto file (e.g. "MARK_TYPE_BOLD")
            # used for proto3 canonical JSON serialization
            super().__setattr__(self, "proto_name", proto_name or name)
            return self

    def __getnewargs_ex__(self) -> Tuple[Tuple[()], Dict[str, Any]]:
        return (), {
            "name": self.name,
            "value": self.value,
            "proto_name": self.proto_name,
        }

    def __str__(self) -> str:
        return self.name or "None"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.{self.name}"

    def __setattr__(self, key: str, value: Any) -> Never:
        raise AttributeError(
            f"{self.__class__.__name__} Cannot reassign a member's attributes."
        )

    def __delattr__(self, item: Any) -> Never:
        raise AttributeError(
            f"{self.__class__.__name__} Cannot delete a member's attributes."
        )

    def __copy__(self) -> Self:
        return self

    def __deepcopy__(self, memo: Any) -> Self:
        return self

    @classmethod
    def try_value(cls, value: int = 0) -> Self:
        """Return the value which corresponds to the value.

        Parameters
        -----------
        value: :class:`int`
            The value of the enum member to get.

        Returns
        -------
        :class:`Enum`
            The corresponding member or a new instance of the enum if
            ``value`` isn't actually a member.
        """
        try:
            return cls._value_map_[value]
        except (KeyError, TypeError):
            return cls.__new__(cls, name=None, value=value)

    @classmethod
    def from_string(cls, name: str) -> Self:
        """Return the value which corresponds to the string name.

        Accepts both the Python member name (e.g. "BOLD") and the original
        proto name (e.g. "MARK_TYPE_BOLD") per the proto3 JSON spec.

        Parameters
        -----------
        name: :class:`str`
            The name of the enum member to get.

        Raises
        -------
        :exc:`ValueError`
            The member was not found in the Enum.
        """
        # Try stripped Python name first
        member = cls._member_map_.get(name)
        if member is not None:
            return member
        # Try original proto name
        for m in cls._member_map_.values():
            if getattr(m, "proto_name", None) == name:
                return m
        raise ValueError(f"Unknown value {name} for enum {cls.__name__}")
