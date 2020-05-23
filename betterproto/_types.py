from typing import TypeVar

# Bound type variable to allow methods to return `self` of subclasses
T = TypeVar("T", bound="Message")
ST = TypeVar("ST", bound="IProtoMessage")
