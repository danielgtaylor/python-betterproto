from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from . import Message
    from grpclib._protocols import IProtoMessage

# Bound type variable to allow methods to return `self` of subclasses
T = TypeVar("T", bound="Message")
ST = TypeVar("ST", bound="IProtoMessage")
