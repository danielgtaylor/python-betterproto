from typing import TYPE_CHECKING


from typing import TYPE_CHECKING, Tuple, Optional, Any

if TYPE_CHECKING:
    from .message import Message


def serialized_on_wire(message: "Message") -> bool:
    """
    If this message was or should be serialized on the wire. This can be used to detect
    presence (e.g. optional wrapper message) and is used internally during
    parsing/serialization.

    Returns
    --------
    :class:`bool`
        Whether this message was or should be serialized on the wire.
    """
    return message._serialized_on_wire


def which_one_of(message: "Message", group_name: str) -> Tuple[str, Optional[Any]]:
    """
    Return the name and value of a message's one-of field group.

    Returns
    --------
    Tuple[:class:`str`, Any]
        The field name and the value for that field.
    """
    field_name = message._group_current.get(group_name)
    if not field_name:
        return "", None
    return field_name, getattr(message, field_name)
