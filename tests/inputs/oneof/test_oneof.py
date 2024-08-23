import pytest

import betterproto
from tests.output_betterproto.oneof import (
    MixedDrink,
    Operation,
    Test,
)
from tests.output_betterproto_pydantic.oneof import (
    Operation as OperationPyd2,
    OperationPing as OperationPingPyd2,
    OperationPong as OperationPongPyd2,
    Test as TestPyd2,
)

# from tests.output_betterproto_pydantic_optionals.oneof import (
from tests.output_betterproto_pydantic_optionals.oneof import (
    MixedDrink as MixedDrinkPyd,
    Operation as OperationPyd,
    OperationPing as OperationPingPyd,
    OperationPong as OperationPongPyd,
)
from tests.util import get_test_case_json_data


def test_which_count():
    message = Test()
    message.from_json(get_test_case_json_data("oneof")[0].json)
    assert betterproto.which_one_of(message, "foo") == ("pitied", 100)


def test_which_name():
    message = Test()
    message.from_json(get_test_case_json_data("oneof", "oneof_name.json")[0].json)
    assert betterproto.which_one_of(message, "foo") == ("pitier", "Mr. T")


def test_which_count_pyd():
    message = TestPyd2(pitier="Mr. T", just_a_regular_field=2, bar_name="a_bar")
    assert betterproto.which_one_of(message, "foo") == ("pitier", "Mr. T")


def test_oneof_constructor_assign():
    message = Test(mixed_drink=MixedDrink(shots=42))
    field, value = betterproto.which_one_of(message, "bar")
    assert field == "mixed_drink"
    assert value.shots == 42


def test_oneof_constructor_pydantic_optionals():
    message = OperationPyd(
        sequence_id=-1,
        ping=OperationPingPyd(),
    )
    message2 = Operation().FromString(bytes(message))
    message3 = OperationPyd().FromString(bytes(message))
    assert message == message3
    assert bytes(message2) == bytes(message3)

    with pytest.raises(ValueError):
        OperationPyd(
            sequence_id=-1,
            ping=OperationPingPyd(),
            pong=OperationPongPyd(),
        ).FromString(bytes(message))

    # Raises an error unless we define pong, which also will trigger another error
    # Since oneof fields group is expecting only one field set.

    with pytest.raises(ValueError):
        OperationPyd2(
            sequence_id=-1,
            ping=OperationPingPyd2(),
        ).FromString(bytes(message))
    with pytest.raises(ValueError):
        OperationPyd2(
            sequence_id=-1,
            ping=OperationPingPyd2(),
            pong=OperationPongPyd2(),
        ).FromString(bytes(message))


# Issue #305:
@pytest.mark.xfail
def test_oneof_nested_assign():
    message = Test()
    message.mixed_drink.shots = 42
    field, value = betterproto.which_one_of(message, "bar")
    assert field == "mixed_drink"
    assert value.shots == 42
