from __future__ import annotations

from typing import (
    Any,
    Callable,
    Generic,
    Optional,
    Type,
    TypeVar,
)

from typing_extensions import (
    Concatenate,
    ParamSpec,
    Self,
)


SelfT = TypeVar("SelfT")
P = ParamSpec("P")
HybridT = TypeVar("HybridT", covariant=True)


class hybridmethod(Generic[SelfT, P, HybridT]):
    def __init__(
        self,
        func: Callable[
            Concatenate[type[SelfT], P], HybridT
        ],  # Must be the classmethod version
    ):
        self.cls_func = func
        self.__doc__ = func.__doc__

    def instancemethod(self, func: Callable[Concatenate[SelfT, P], HybridT]) -> Self:
        self.instance_func = func
        return self

    def __get__(
        self, instance: Optional[SelfT], owner: Type[SelfT]
    ) -> Callable[P, HybridT]:
        if instance is None or self.instance_func is None:
            # either bound to the class, or no instance method available
            return self.cls_func.__get__(owner, None)
        return self.instance_func.__get__(instance, owner)


T_co = TypeVar("T_co")
TT_co = TypeVar("TT_co", bound="type[Any]")


class classproperty(Generic[TT_co, T_co]):
    def __init__(self, func: Callable[[TT_co], T_co]):
        self.__func__ = func

    def __get__(self, instance: Any, type: TT_co) -> T_co:
        return self.__func__(type)
