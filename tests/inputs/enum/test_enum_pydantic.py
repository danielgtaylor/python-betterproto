import pydantic

from tests.output_betterproto_pydantic.enum import (
    ArithmeticOperator,
    Choice,
    Test,
)


def test_enum_set_and_get():
    assert Test(choice=Choice.ZERO, choices=[]).choice == Choice.ZERO
    assert Test(choice=Choice.ONE, choices=[]).choice == Choice.ONE
    assert Test(choice=Choice.THREE, choices=[]).choice == Choice.THREE
    assert Test(choice=Choice.FOUR, choices=[]).choice == Choice.FOUR


def test_enum_set_with_int():
    assert Test(choice=0, choices=[]).choice == Choice.ZERO
    assert Test(choice=1, choices=[]).choice == Choice.ONE
    assert Test(choice=3, choices=[]).choice == Choice.THREE
    assert Test(choice=4, choices=[]).choice == Choice.FOUR


def test_enum_is_comparable_with_int():
    assert Test(choice=Choice.ZERO, choices=[]).choice == 0
    assert Test(choice=Choice.ONE, choices=[]).choice == 1
    assert Test(choice=Choice.THREE, choices=[]).choice == 3
    assert Test(choice=Choice.FOUR, choices=[]).choice == 4


def test_enum_to_dict():
    assert (
        "choice" not in Test(choice=Choice.ZERO, choices=[]).to_dict()
    ), "Default enum value is not serialized"
    assert (
        Test(choice=Choice.ZERO, choices=[]).to_dict(include_default_values=True)[
            "choices"
        ]
        == []
    )
    assert (
        Test(choice=Choice.ZERO, choices=[]).to_dict(include_default_values=True)[
            "choice"
        ]
        == "ZERO"
    )
    assert Test(choice=Choice.ONE, choices=[]).to_dict()["choice"] == "ONE"
    assert Test(choice=Choice.THREE, choices=[]).to_dict()["choice"] == "THREE"
    assert Test(choice=Choice.FOUR, choices=[]).to_dict()["choice"] == "FOUR"


def test_repeated_enum_is_comparable_with_int():
    assert Test(choices=[Choice.ZERO], choice=0).choices == [0]
    assert Test(choices=[Choice.ONE], choice=0).choices == [1]
    assert Test(choices=[Choice.THREE], choice=0).choices == [3]
    assert Test(choices=[Choice.FOUR], choice=0).choices == [4]


def test_repeated_enum_set_and_get():
    assert Test(choices=[Choice.ZERO], choice=0).choices == [Choice.ZERO]
    assert Test(choices=[Choice.ONE], choice=0).choices == [Choice.ONE]
    assert Test(choices=[Choice.THREE], choice=0).choices == [Choice.THREE]
    assert Test(choices=[Choice.FOUR], choice=0).choices == [Choice.FOUR]


def test_repeated_enum_to_dict():
    assert Test(choices=[Choice.ZERO], choice=0).to_dict()["choices"] == ["ZERO"]
    assert Test(choices=[Choice.ONE], choice=0).to_dict()["choices"] == ["ONE"]
    assert Test(choices=[Choice.THREE], choice=0).to_dict()["choices"] == ["THREE"]
    assert Test(choices=[Choice.FOUR], choice=0).to_dict()["choices"] == ["FOUR"]

    all_enums_dict = Test(
        choices=[Choice.ZERO, Choice.ONE, Choice.THREE, Choice.FOUR], choice=0
    ).to_dict()
    assert (all_enums_dict["choices"]) == ["ZERO", "ONE", "THREE", "FOUR"]


def test_repeated_enum_with_single_value_to_dict_but_pydantic_validation():
    is_failed = False
    try:
        assert Test(choices=Choice.ONE).to_dict()["choices"] == ["ONE"]
    except pydantic.error_wrappers.ValidationError:
        is_failed = True
    assert is_failed, "Should fail due to pydantic validation"
    is_failed = False
    try:
        assert Test(choices=1).to_dict()["choices"] == ["ONE"]
    except pydantic.error_wrappers.ValidationError:
        is_failed = True
    assert is_failed, "Should fail due to pydantic validation"


def test_repeated_enum_with_non_list_iterables_to_dict():
    assert Test(choices=(1, 3), choice=0).to_dict()["choices"] == ["ONE", "THREE"]
    assert Test(choices=(1, 3), choice=0).to_dict()["choices"] == ["ONE", "THREE"]
    assert Test(choices=(Choice.ONE, Choice.THREE), choice=0).to_dict()["choices"] == [
        "ONE",
        "THREE",
    ]

    def enum_generator():
        yield Choice.ONE
        yield Choice.THREE

    assert Test(choices=enum_generator(), choice=0).to_dict()["choices"] == [
        "ONE",
        "THREE",
    ]


def test_enum_mapped_on_parse():
    # test default value
    gen_default_value = lambda: Test(choice=Choice.ZERO, choices=[])
    b = gen_default_value().parse(bytes(gen_default_value()))
    assert b.choice.name == Choice.ZERO.name
    assert b.choices == []

    # test non default value
    a = gen_default_value().parse(bytes(Test(choice=Choice.ONE, choices=[])))
    assert a.choice.name == Choice.ONE.name
    assert b.choices == []

    # test repeated
    c = gen_default_value().parse(
        bytes(Test(choices=[Choice.THREE, Choice.FOUR], choice=Choice.ZERO))
    )
    assert c.choices[0].name == Choice.THREE.name
    assert c.choices[1].name == Choice.FOUR.name

    # bonus: defaults after empty init are also mapped
    assert gen_default_value().choice.name == Choice.ZERO.name


def test_renamed_enum_members():
    assert set(ArithmeticOperator.__members__) == {
        "NONE",
        "PLUS",
        "MINUS",
        "_0_PREFIXED",
    }
