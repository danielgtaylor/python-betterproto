from typing import (
    TYPE_CHECKING,
    TypeVar,
)


if TYPE_CHECKING:
    from grpclib._typing import IProtoMessage

    from . import Message

# Bound type variable to allow methods to return `self` of subclasses
T = TypeVar("T", bound="Message")
ST = TypeVar("ST", bound="IProtoMessage")
