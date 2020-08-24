"""
MIT License

Copyright (c) 2018 Adrian Stachlewski

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Sped up version of https://github.com/starhel/dataslots 's implementation
"""

from dataclasses import fields
from typing import TYPE_CHECKING, Type, TypeVar

if TYPE_CHECKING:
    import betterproto

__all__ = ("dataslots",)

T = TypeVar("T", bound=Type["betterproto.Message"])


def dataslots(cls: T) -> T:
    """
    A decorator to add :ref:`__slots__` to a class created by
    :func:`dataclasses.dataclass`.

    Returns
    -------
    A new dataclass with the same properties as the old dataclass, just without a
    ``__dict__`` attribute and instead with ``__slots__``, thus saving memory, attribute
    access speed etc.
    """
    # we have no need for wrap as we always call it without params and setstate
    # related functions as we don't use frozen.

    inherited_slots = set(getattr(base, "__slots__", ()) for base in cls.__mro__)
    # cls.mro() vs cls.__mro__ is about 2x faster
    # Then simplifying the comprhension is about a 1.5x improvement over the old way
    field_names = set(f.name for f in fields(cls))

    cls_dict = cls.__dict__.copy()  # About 4x faster than dict(cls.__dict__)
    cls_dict["__slots__"] = tuple(field_names - inherited_slots)

    # del in favour of pop as any item is always going to be in the class' __dict__
    # Erase field, __dict__ and __weakref__ names from class __dict__
    for name in field_names:
        del cls_dict[name]
    del cls_dict["__dict__"]
    del cls_dict["__weakref__"]

    # Prepare the new slotted class
    # type(cls) vs cls.__class__ is about 2x faster again
    new_cls = cls.__class__(cls.__name__, cls.__bases__, cls_dict)
    new_cls.__qualname__ = cls.__qualname__

    return new_cls
