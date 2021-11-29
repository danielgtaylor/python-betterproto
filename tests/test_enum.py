from typing import Tuple, Optional

import pytest

import betterproto


class Colour(betterproto.Enum):
    RED = 1
    GREEN = 2
    BLUE = 3


PURPLE = Colour.__new__(Colour, name=None, value=4)


@pytest.mark.parametrize(
    "member, str_value",
    [
        (Colour.RED, "RED"),
        (Colour.GREEN, "GREEN"),
        (Colour.BLUE, "BLUE"),
    ],
)
def test_str(member: Colour, str_value: str) -> None:
    assert str(member) == str_value


@pytest.mark.parametrize(
    "member, repr_value",
    [
        (Colour.RED, "Colour.RED"),
        (Colour.GREEN, "Colour.GREEN"),
        (Colour.BLUE, "Colour.BLUE"),
    ],
)
def test_repr(member: Colour, repr_value: str) -> None:
    assert repr(member) == repr_value


@pytest.mark.parametrize(
    "member, values",
    [
        (Colour.RED, ("RED", 1)),
        (Colour.GREEN, ("GREEN", 2)),
        (Colour.BLUE, ("BLUE", 3)),
        (PURPLE, (None, 4)),
    ],
)
def test_name_values(member: Colour, values: Tuple[Optional[str], int]) -> None:
    assert (member.name, member.value) == values


@pytest.mark.parametrize(
    "member, input_str",
    [
        (Colour.RED, "RED"),
        (Colour.GREEN, "GREEN"),
        (Colour.BLUE, "BLUE"),
    ],
)
def test_from_string(member: Colour, input_str: str) -> None:
    assert Colour.from_string(input_str) == member


@pytest.mark.parametrize(
    "member, input_int",
    [
        (Colour.RED, 1),
        (Colour.GREEN, 2),
        (Colour.BLUE, 3),
        (PURPLE, 4),
    ],
)
def test_try_value(member: Colour, input_int: int) -> None:
    assert Colour.try_value(input_int) == member
