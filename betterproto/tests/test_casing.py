import pytest

from betterproto.casing import camel_case, pascal_case, snake_case


@pytest.mark.parametrize(
    ["value", "expected"],
    [
        ("", ""),
        ("a", "A"),
        ("foobar", "Foobar"),
        ("FooBar", "FooBar"),
        ("foo.bar", "FooBar"),
        ("foo_bar", "FooBar"),
        ("FOOBAR", "Foobar"),
        ("FOOBar", "FooBar"),
        ("UInt32", "UInt32"),
        ("FOO_BAR", "FooBar"),
        ("FOOBAR1", "Foobar1"),
        ("FOOBAR_1", "Foobar1"),
        ("FOO1BAR2", "Foo1Bar2"),
        ("foo__bar", "FooBar"),
        ("_foobar", "Foobar"),
        ("foobaR", "FoobaR"),
        ("foo~bar", "FooBar"),
        ("foo:bar", "FooBar"),
        ("1foobar", "1Foobar"),
    ],
)
def test_pascal_case(value, expected):
    actual = pascal_case(value)
    assert actual == expected, f"{value} => {expected} (actual: {actual})"


@pytest.mark.parametrize(
    ["value", "expected"],
    [
        ("", ""),
        ("a", "a"),
        ("foobar", "foobar"),
        ("FooBar", "fooBar"),
        ("foo.bar", "fooBar"),
        ("foo_bar", "fooBar"),
        ("FOOBAR", "foobar"),
        ("FOO_BAR", "fooBar"),
        ("FOOBAR1", "foobar1"),
        ("FOOBAR_1", "foobar1"),
        ("FOO1BAR2", "foo1Bar2"),
        ("foo__bar", "fooBar"),
        ("_foobar", "foobar"),
        ("foobaR", "foobaR"),
        ("foo~bar", "fooBar"),
        ("foo:bar", "fooBar"),
        ("1foobar", "1Foobar"),
    ],
)
def test_camel_case(value, expected):
    actual = camel_case(value)
    assert actual == expected, f"{value} => {expected} (actual: {actual})"


@pytest.mark.parametrize(
    ["value", "expected"],
    [
        ("", ""),
        ("a", "a"),
        ("foobar", "foobar"),
        ("FooBar", "foo_bar"),
        ("foo.bar", "foo_bar"),
        ("foo_bar", "foo_bar"),
        ("FOOBAR", "foobar"),
        ("FOOBar", "foo_bar"),
        ("UInt32", "u_int32"),
        ("FOO_BAR", "foo_bar"),
        ("FOOBAR1", "foobar1"),
        ("FOOBAR_1", "foobar_1"),
        ("FOOBAR_123", "foobar_123"),
        ("FOO1BAR2", "foo1_bar2"),
        ("foo__bar", "foo_bar"),
        ("_foobar", "foobar"),
        ("foobaR", "fooba_r"),
        ("foo~bar", "foo_bar"),
        ("foo:bar", "foo_bar"),
        ("1foobar", "1_foobar"),
    ],
)
def test_snake_case(value, expected):
    actual = snake_case(value)
    assert actual == expected, f"{value} => {expected} (actual: {actual})"
