import importlib
import json
import os
import sys
from collections import namedtuple
from typing import Set

import pytest

import betterproto
from betterproto.tests.inputs import config as test_input_config
from betterproto.tests.mocks import MockChannel
from betterproto.tests.util import get_directories, get_test_case_json_data, inputs_path

# Force pure-python implementation instead of C++, otherwise imports
# break things because we can't properly reset the symbol database.
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

from google.protobuf import symbol_database
from google.protobuf.descriptor_pool import DescriptorPool
from google.protobuf.json_format import Parse


class TestCases:
    def __init__(self, path, services: Set[str], xfail: Set[str]):
        _all = set(get_directories(path))
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
    xfail=test_input_config.tests,
)

plugin_output_package = "betterproto.tests.output_betterproto"
reference_output_package = "betterproto.tests.output_reference"


TestData = namedtuple("TestData", "plugin_module, reference_module, json_data")


@pytest.fixture
def test_data(request):
    test_case_name = request.param

    # Reset the internal symbol database so we can import the `Test` message
    # multiple times. Ugh.
    sym = symbol_database.Default()
    sym.pool = DescriptorPool()

    reference_module_root = os.path.join(
        *reference_output_package.split("."), test_case_name
    )

    sys.path.append(reference_module_root)

    yield (
        TestData(
            plugin_module=importlib.import_module(
                f"{plugin_output_package}.{test_case_name}.{test_case_name}"
            ),
            reference_module=lambda: importlib.import_module(
                f"{reference_output_package}.{test_case_name}.{test_case_name}_pb2"
            ),
            json_data=get_test_case_json_data(test_case_name),
        )
    )

    sys.path.remove(reference_module_root)


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
        message: betterproto.Message = plugin_module.Test()

        message.from_json(json_data)
        message_json = message.to_json(0)

        assert json.loads(message_json) == json.loads(json_data)


@pytest.mark.parametrize("test_data", test_cases.services, indirect=True)
def test_service_can_be_instantiated(test_data: TestData) -> None:
    plugin_module, _, json_data = test_data
    plugin_module.TestStub(MockChannel())


@pytest.mark.parametrize("test_data", test_cases.messages_with_json, indirect=True)
def test_binary_compatibility(repeat, test_data: TestData) -> None:
    plugin_module, reference_module, json_data = test_data

    reference_instance = Parse(json_data, reference_module().Test())
    reference_binary_output = reference_instance.SerializeToString()

    for _ in range(repeat):
        plugin_instance_from_json: betterproto.Message = plugin_module.Test().from_json(
            json_data
        )
        plugin_instance_from_binary = plugin_module.Test.FromString(
            reference_binary_output
        )

        # # Generally this can't be relied on, but here we are aiming to match the
        # # existing Python implementation and aren't doing anything tricky.
        # # https://developers.google.com/protocol-buffers/docs/encoding#implications
        assert bytes(plugin_instance_from_json) == reference_binary_output
        assert bytes(plugin_instance_from_binary) == reference_binary_output

        assert plugin_instance_from_json == plugin_instance_from_binary
        assert (
            plugin_instance_from_json.to_dict() == plugin_instance_from_binary.to_dict()
        )
