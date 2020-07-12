import pytest

from betterproto.enum import Enum, IntEnum


class Season(Enum):
    SPRING = 1
    SUMMER = 2
    AUTUMN = 3
    WINTER = 4


class Grades(IntEnum):
    A = 5
    B = 4
    C = 3
    D = 2
    F = 0


class Directional(Enum):
    EAST = "east"
    WEST = "west"
    NORTH = "north"
    SOUTH = "south"


def test_dir_on_class():
    assert set(dir(Season)) == {
        "__class__",
        "__doc__",
        "__members__",
        "__module__",
        "SPRING",
        "SUMMER",
        "AUTUMN",
        "WINTER",
    }


def test_enum_in_enum_out():
    assert Season(Season.WINTER) is Season.WINTER


def test_enum_value():
    assert Season.SPRING.value == 1


def test_enum():
    lst = list(Season)
    assert len(lst) == len(Season)
    assert len(Season) == 4
    assert [Season.SPRING, Season.SUMMER, Season.AUTUMN, Season.WINTER] == lst

    for i, season in enumerate("SPRING SUMMER AUTUMN WINTER".split(), 1):
        e = Season(i)
        assert e == getattr(Season, season)
        assert e.value == i
        assert e == i
        assert e.name == season
        assert e in Season
        assert type(e) is Season
        assert isinstance(e, Season)
        assert str(e) == f"Season.{season}"
        assert repr(e) == f"<Season.{season}: {i}>"


def test_value_name():
    assert Season.SPRING.name == "SPRING"
    assert Season.SPRING.value == 1


def test_changing_member():
    with pytest.raises(AttributeError):
        Season.WINTER = "really cold"


def test_attribute_deletion():
    class Season(Enum):
        SPRING = 1
        SUMMER = 2
        AUTUMN = 3
        WINTER = 4

        def spam(cls):
            pass

    with pytest.raises(AttributeError):
        del Season.DRY


def test_bool_of_class():
    class Empty(Enum):
        pass

    assert bool(Empty)


def test_bool_of_member():
    class Count(Enum):
        zero = 0
        one = 1
        two = 2

    for member in Count:
        assert bool(member)


def test_bool():
    # plain Enum members are always True
    class Logic(Enum):
        true = True
        false = False

    assert Logic.true
    assert Logic.false

    # unless overridden
    class RealLogic(Enum):
        true = True
        false = False

        def __bool__(self):
            return bool(self.value)

    assert RealLogic.true
    assert not RealLogic.false

    # mixed Enums depend on mixed-in type
    class IntLogic(int, Enum):
        true = 1
        false = 0

    assert IntLogic.true
    assert not IntLogic.false


def test_contains():
    assert Season.AUTUMN in Season
    with pytest.raises(TypeError):
        3 in Season
    with pytest.raises(TypeError):
        "AUTUMN" in Season

    val = Season(3)
    assert val in Season

    class OtherEnum(Enum):
        one = 1
        two = 2

    assert OtherEnum.two not in Season


def test_comparisons():
    with pytest.raises(TypeError):
        Season.SPRING < Season.WINTER
    with pytest.raises(TypeError):
        Season.SPRING > 4

    assert Season.SPRING != 1

    class Part(Enum):
        SPRING = 1
        CLIP = 2
        BARREL = 3

    assert Season.SPRING != Part.SPRING
    with pytest.raises(TypeError):
        Season.SPRING < Part.CLIP


def test_enum_duplicates():
    class Season(Enum):
        SPRING = 1
        SUMMER = 2
        AUTUMN = FALL = 3
        WINTER = 4
        ANOTHER_SPRING = 1

    lst = list(Season)
    assert lst == [Season.SPRING, Season.SUMMER, Season.AUTUMN, Season.WINTER]
    assert Season.FALL is Season.AUTUMN
    assert Season.FALL.value == 3
    assert Season.AUTUMN.value == 3
    assert Season(3) is Season.AUTUMN
    assert Season(1) is Season.SPRING
    assert Season.FALL.name == "AUTUMN"
    assert [k for k, v in Season.__members__.items() if v.name != k] == [
        "FALL",
        "ANOTHER_SPRING",
    ]


def test_enum_with_value_name():
    class Huh(Enum):
        name = 1
        value = 2

    assert list(Huh) == [Huh.name, Huh.value]
    assert Huh.name.name == "name"
    assert Huh.name.value == 1


def test_hash():
    dates = {}
    dates[Season.WINTER] = "1225"
    dates[Season.SPRING] = "0315"
    dates[Season.SUMMER] = "0704"
    dates[Season.AUTUMN] = "1031"
    assert dates[Season.AUTUMN] == "1031"


def test_intenum():
    class WeekDay(IntEnum):
        SUNDAY = 1
        MONDAY = 2
        TUESDAY = 3
        WEDNESDAY = 4
        THURSDAY = 5
        FRIDAY = 6
        SATURDAY = 7

    assert ["a", "b", "c"][WeekDay.MONDAY] == "c"
    assert [i for i in range(WeekDay.TUESDAY)] == [0, 1, 2]

    lst = list(WeekDay)
    assert len(lst) == len(WeekDay)
    assert len(WeekDay) == 7
    target = "SUNDAY MONDAY TUESDAY WEDNESDAY THURSDAY FRIDAY SATURDAY"
    target = target.split()
    for i, weekday in enumerate(target, 1):
        e = WeekDay(i)
        assert e == i
        assert int(e) == i
        assert e.name == weekday
        assert e in WeekDay
        assert lst.index(e) + 1 == i
        assert 0 < e < 8
        assert type(e) is WeekDay
        assert isinstance(e, int)
        assert isinstance(e, Enum)
