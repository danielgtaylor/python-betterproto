import importlib
import json
import os
import sys
import pytest
import betterproto
from betterproto.tests.util import get_directories, inputs_path
from collections import namedtuple

# Force pure-python implementation instead of C++, otherwise imports
# break things because we can't properly reset the symbol database.
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

from google.protobuf import symbol_database
from google.protobuf.descriptor_pool import DescriptorPool
from google.protobuf.json_format import Parse


excluded_test_cases = {"googletypes_response", "service"}
test_case_names = {*get_directories(inputs_path)} - excluded_test_cases

plugin_output_package = "betterproto.tests.output_betterproto"
reference_output_package = "betterproto.tests.output_reference"


TestData = namedtuple("TestData", "plugin_module, reference_module, json_data")


@pytest.fixture(scope="module", params=test_case_names)
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

    yield TestData(
        plugin_module=importlib.import_module(
            f"{plugin_output_package}.{test_case_name}.{test_case_name}"
        ),
        reference_module=importlib.import_module(
            f"{reference_output_package}.{test_case_name}.{test_case_name}_pb2"
        ),
        json_data=get_test_case_json_data(test_case_name),
    )

    sys.path.remove(reference_module_root)


def test_message_can_instantiated(test_data: TestData) -> None:
    plugin_module, *_ = test_data
    plugin_module.Test()


def test_message_equality(test_data: TestData) -> None:
    plugin_module, *_ = test_data
    message1 = plugin_module.Test()
    message2 = plugin_module.Test()
    assert message1 == message2


def test_message_json(repeat, test_data: TestData) -> None:
    plugin_module, _, json_data = test_data

    for _ in range(repeat):
        message: betterproto.Message = plugin_module.Test()

        message.from_json(json_data)
        message_json = message.to_json(0)

        assert json.loads(json_data) == json.loads(message_json)


def test_binary_compatibility(repeat, test_data: TestData) -> None:
    plugin_module, reference_module, json_data = test_data

    reference_instance = Parse(json_data, reference_module.Test())
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
        assert plugin_instance_from_json == plugin_instance_from_binary
        assert (
            plugin_instance_from_json.to_dict() == plugin_instance_from_binary.to_dict()
        )


"""
helper methods
"""


def get_test_case_json_data(test_case_name):
    test_data_path = os.path.join(inputs_path, test_case_name, f"{test_case_name}.json")
    if not os.path.exists(test_data_path):
        return None

    with open(test_data_path) as fh:
        return fh.read()
