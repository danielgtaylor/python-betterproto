import pytest

from betterproto.enums import Enum, IntEnum


class Season(IntEnum):
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


def test_dir_on_item():
    assert set(dir(Season.WINTER)) == {
        "__class__",
        "__doc__",
        "__module__",
        "name",
        "value",
    }


def test_dir_with_added_behavior():
    class Test(Enum):
        this = "that"
        these = "those"

        def wowser(self):
            return f"Wowser! I'm {name}!"

    assert set(dir(Test)) == {
        "__class__",
        "__doc__",
        "__members__",
        "__module__",
        "this",
        "these",
    }
    assert set(dir(Test.this)) == {
        "__class__",
        "__doc__",
        "__module__",
        "name",
        "value",
        "wowser",
    }


def test_dir_on_sub_with_behavior_on_super():
    class SuperEnum(Enum):
        def invisible(self):
            return "did you see me?"

    class SubEnum(SuperEnum):
        sample = 5

    assert set(dir(SubEnum.sample)) == {
        "__class__",
        "__doc__",
        "__module__",
        "name",
        "value",
        "invisible",
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
        assert e != i
        assert e.name == season
        assert e in Season
        assert type(e) is Season
        assert isinstance(e, Season)
        assert str(e) == f"Season.{season}"
        assert repr(e) == f"<Season.{season}: {i}>"


def test_value_name():
    assert Season.SPRING.name == "SPRING"
    assert Season.SPRING.value == 1
    with pytest.raises(AttributeError):
        Season.SPRING.name = "invierno"
    with pytest.raises(AttributeError):
        Season.SPRING.value = 2


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

    assert hasattr(Season, "spam")
    with pytest.raises(AttributeError):
        del Season.spam
    assert not hasattr(Season, "spam")

    del Season.SPRING

    with pytest.raises(AttributeError):
        del Season.DRY
    with pytest.raises(AttributeError):
        del Season.SPRING.name


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
    assert not Logic.false

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
    assert type(Huh.name) is Huh
    assert Huh.name.name == "name"
    assert Huh.name.value == 1


def test_format_enum():
    assert "{}".format(Season.SPRING) == "{}".format(str(Season.SPRING))
    assert "{:}".format(Season.SPRING) == "{:}".format(str(Season.SPRING))
    assert "{:20}".format(Season.SPRING) == "{:20}".format(str(Season.SPRING))
    assert "{:^20}".format(Season.SPRING) == "{:^20}".format(str(Season.SPRING))
    assert "{:>20}".format(Season.SPRING) == "{:>20}".format(str(Season.SPRING))
    assert "{:<20}".format(Season.SPRING) == "{:<20}".format(str(Season.SPRING))


def test_format_override_enum():
    class EnumWithFormatOverride(Enum):
        one = 1.0
        two = 2.0

        def __format__(self, spec):
            return "Format!!"

    assert str(EnumWithFormatOverride.one) == "EnumWithFormatOverride.one"
    assert "{}".format(EnumWithFormatOverride.one) == "Format!!"


def test_str_override_mixin():
    class MixinEnumWithStrOverride(float, Enum):
        one = 1.0
        two = 2.0

        def __str__(self):
            return "Overridden!"

    assert str(MixinEnumWithStrOverride.one) == "Overridden!"
    assert "{}".format(MixinEnumWithStrOverride.one) == "Overridden!"


def test_str_and_format_override_mixin():
    class MixinWithStrFormatOverrides(float, Enum):
        one = 1.0
        two = 2.0

        def __str__(self):
            return "Str!"

        def __format__(self, spec):
            return "Format!"

    assert str(MixinWithStrFormatOverrides.one) == "Str!"
    assert "{}".format(MixinWithStrFormatOverrides.one) == "Format!"


def test_format_override_mixin():
    class TestFloat(float, Enum):
        one = 1.0
        two = 2.0

        def __format__(self, spec):
            return "TestFloat success!"

    assert str(TestFloat.one) == "TestFloat.one"
    assert "{}".format(TestFloat.one) == "TestFloat success!"


def assert_format_is_value(spec, member):
    assert spec.format(member) == spec.format(member.value)


def test_format_enum_int():
    assert_format_is_value("{}", Grades.C)
    assert_format_is_value("{:}", Grades.C)
    assert_format_is_value("{:20}", Grades.C)
    assert_format_is_value("{:^20}", Grades.C)
    assert_format_is_value("{:>20}", Grades.C)
    assert_format_is_value("{:<20}", Grades.C)
    assert_format_is_value("{:+}", Grades.C)
    assert_format_is_value("{:08X}", Grades.C)
    assert_format_is_value("{:b}", Grades.C)


def test_format_enum_str():
    assert_format_is_value("{}", Directional.WEST)
    assert_format_is_value("{:}", Directional.WEST)
    assert_format_is_value("{:20}", Directional.WEST)
    assert_format_is_value("{:^20}", Directional.WEST)
    assert_format_is_value("{:>20}", Directional.WEST)
    assert_format_is_value("{:<20}", Directional.WEST)


def test_hash():
    dates = {}
    dates[Season.WINTER] = "1225"
    dates[Season.SPRING] = "0315"
    dates[Season.SUMMER] = "0704"
    dates[Season.AUTUMN] = "1031"
    assert dates[Season.AUTUMN] == "1031"


def test_intenum_from_scratch():
    class phy(int, Enum):
        pi = 3
        tau = 2 * pi

    assert phy.pi < phy.tau


def test_intenum_inherited():
    class IntEnum(int, Enum):
        pass

    class phy(IntEnum):
        pi = 3
        tau = 2 * pi

    assert phy.pi < phy.tau


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
