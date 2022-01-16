import enum

__all__ = ("Enum",)


class Enum(enum.IntEnum):
    """
    The base class for protobuf enumerations, all generated enumerations will inherit
    from this. Bases :class:`enum.IntEnum`.
    """

    @classmethod
    def from_string(cls, name: str) -> "Enum":
        """Return the value which corresponds to the string name.

        Parameters
        -----------
        name: :class:`str`
            The name of the enum member to get

        Raises
        -------
        :exc:`ValueError`
            The member was not found in the Enum.
        """
        try:
            return cls._member_map_[name]  # type: ignore
        except KeyError as e:
            raise ValueError(f"Unknown value {name} for enum {cls.__name__}") from e
