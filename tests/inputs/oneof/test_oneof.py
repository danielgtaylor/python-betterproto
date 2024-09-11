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
    OperationStatus as OperationStatusPyd,
    OperationStatusModule as OperationStatusModulePyd,
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
    msg_ctrstr_arr = OperationStatusPyd(
        strings=["asdf", "asdasdasd", "asdasdasd", "sd"],
    )
    msg_ctrstr_arr3 = OperationStatusPyd().FromString(bytes(msg_ctrstr_arr))
    assert msg_ctrstr_arr == msg_ctrstr_arr3

    _histo_sample = {
        1: 100,
        2: 500,
        3: 600,
        4: 700,
        8: 999999999,
    }
    msg_ctr_arr = OperationPyd(
        sequence_id=1,
        status=OperationStatusPyd(
            fractions=[1, 2, 3, 4, 5, 6, 7, 8, 9, 0],
            histo=_histo_sample,
            strings=["asdf", "asdasdasd", "asdasdasd", "sd"],
            modules=[
                OperationStatusModulePyd(
                    name="http_client_generic_response_time",
                    histo=_histo_sample,
                ),
                OperationStatusModulePyd(
                    name="http_server_generic_response_time",
                    histo=_histo_sample,
                ),
            ],
        ),
    )
    msg_ctr_arr2 = Operation().FromString(bytes(msg_ctr_arr))
    msg_ctr_arr3 = OperationPyd().FromString(bytes(msg_ctr_arr))
    assert msg_ctr_arr == msg_ctr_arr3
    assert bytes(msg_ctr_arr) == bytes(msg_ctr_arr3)
    assert msg_ctr_arr.to_dict() == msg_ctr_arr3.to_dict()

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
            status=OperationStatusPyd(),
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
