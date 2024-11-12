import importlib
import json
import math
import os
import sys
from collections import namedtuple
from types import ModuleType
from typing import (
    Any,
    Dict,
    List,
    Set,
    Tuple,
)

import pytest

import betterproto
from tests.inputs import config as test_input_config
from tests.mocks import MockChannel
from tests.util import (
    find_module,
    get_directories,
    get_test_case_json_data,
    inputs_path,
)


# Force pure-python implementation instead of C++, otherwise imports
# break things because we can't properly reset the symbol database.
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

from google.protobuf.json_format import Parse


class TestCases:
    def __init__(
        self,
        path,
        services: Set[str],
        xfail: Set[str],
    ):
        _all = set(get_directories(path)) - {"__pycache__"}
        _services = services
        _messages = (_all - services) - {"__pycache__"}
        _messages_with_json = {
            test for test in _messages if get_test_case_json_data(test)
        }

        unknown_xfail_tests = xfail - _all
        if unknown_xfail_tests:
            raise Exception(f"Unknown test(s) in config.py: {unknown_xfail_tests}")

        self.all = self.apply_xfail_marks(_all, xfail)
        self.services = self.apply_xfail_marks(_services, xfail)
        self.messages = self.apply_xfail_marks(_messages, xfail)
        self.messages_with_json = self.apply_xfail_marks(_messages_with_json, xfail)

    @staticmethod
    def apply_xfail_marks(test_set: Set[str], xfail: Set[str]):
        return [
            pytest.param(test, marks=pytest.mark.xfail) if test in xfail else test
            for test in test_set
        ]


test_cases = TestCases(
    path=inputs_path,
    services=test_input_config.services,
    xfail=test_input_config.xfail,
)

plugin_output_package = "tests.output_betterproto"
reference_output_package = "tests.output_reference"

TestData = namedtuple("TestData", ["plugin_module", "reference_module", "json_data"])


def module_has_entry_point(module: ModuleType):
    return any(hasattr(module, attr) for attr in ["Test", "TestStub"])


def list_replace_nans(items: List) -> List[Any]:
    """Replace float("nan") in a list with the string "NaN"

    Parameters
    ----------
    items : List
            List to update

    Returns
    -------
    List[Any]
        Updated list
    """
    result = []
    for item in items:
        if isinstance(item, list):
            result.append(list_replace_nans(item))
        elif isinstance(item, dict):
            result.append(dict_replace_nans(item))
        elif isinstance(item, float) and math.isnan(item):
            result.append(betterproto.NAN)
    return result


def dict_replace_nans(input_dict: Dict[Any, Any]) -> Dict[Any, Any]:
    """Replace float("nan") in a dictionary with the string "NaN"

    Parameters
    ----------
    input_dict : Dict[Any, Any]
            Dictionary to update

    Returns
    -------
    Dict[Any, Any]
        Updated dictionary
    """
    result = {}
    for key, value in input_dict.items():
        if isinstance(value, dict):
            value = dict_replace_nans(value)
        elif isinstance(value, list):
            value = list_replace_nans(value)
        elif isinstance(value, float) and math.isnan(value):
            value = betterproto.NAN
        result[key] = value
    return result


@pytest.fixture
def test_data(request, reset_sys_path):
    test_case_name = request.param

    reference_module_root = os.path.join(
        *reference_output_package.split("."), test_case_name
    )
    sys.path.append(reference_module_root)

    plugin_module = importlib.import_module(f"{plugin_output_package}.{test_case_name}")

    plugin_module_entry_point = find_module(plugin_module, module_has_entry_point)

    if not plugin_module_entry_point:
        raise Exception(
            f"Test case {repr(test_case_name)} has no entry point. "
            "Please add a proto message or service called Test and recompile."
        )

    yield (
        TestData(
            plugin_module=plugin_module_entry_point,
            reference_module=lambda: importlib.import_module(
                f"{reference_output_package}.{test_case_name}.{test_case_name}_pb2"
            ),
            json_data=get_test_case_json_data(test_case_name),
        )
    )


@pytest.mark.parametrize("test_data", test_cases.messages, indirect=True)
def test_message_can_instantiated(test_data: TestData) -> None:
    plugin_module, *_ = test_data
    plugin_module.Test()


@pytest.mark.parametrize("test_data", test_cases.messages, indirect=True)
def test_message_equality(test_data: TestData) -> None:
    plugin_module, *_ = test_data
    message1 = plugin_module.Test()
    message2 = plugin_module.Test()
    assert message1 == message2


@pytest.mark.parametrize("test_data", test_cases.messages_with_json, indirect=True)
def test_message_json(repeat, test_data: TestData) -> None:
    plugin_module, _, json_data = test_data

    for _ in range(repeat):
        for sample in json_data:
            if sample.belongs_to(test_input_config.non_symmetrical_json):
                continue

            message: betterproto.Message = plugin_module.Test()

            message.from_json(sample.json)
            message_json = message.to_json(indent=0)

            print(message)
            print(message_json)
            print(message.to_dict())

            assert dict_replace_nans(json.loads(message_json)) == dict_replace_nans(
                json.loads(sample.json)
            )


@pytest.mark.parametrize("test_data", test_cases.services, indirect=True)
def test_service_can_be_instantiated(test_data: TestData) -> None:
    test_data.plugin_module.TestStub(MockChannel())


@pytest.mark.parametrize("test_data", test_cases.messages_with_json, indirect=True)
def test_binary_compatibility(repeat, test_data: TestData) -> None:
    plugin_module, reference_module, json_data = test_data

    for sample in json_data:
        reference_instance = Parse(sample.json, reference_module().Test())
        reference_binary_output = reference_instance.SerializeToString()

        for _ in range(repeat):
            plugin_instance_from_json: betterproto.Message = (
                plugin_module.Test().from_json(sample.json)
            )
            plugin_instance_from_binary = plugin_module.Test.FromString(
                reference_binary_output
            )

            # Generally this can't be relied on, but here we are aiming to match the
            # existing Python implementation and aren't doing anything tricky.
            # https://developers.google.com/protocol-buffers/docs/encoding#implications
            assert bytes(plugin_instance_from_json) == reference_binary_output
            assert bytes(plugin_instance_from_binary) == reference_binary_output

            assert plugin_instance_from_json == plugin_instance_from_binary
            assert dict_replace_nans(
                plugin_instance_from_json.to_dict()
            ) == dict_replace_nans(plugin_instance_from_binary.to_dict())
