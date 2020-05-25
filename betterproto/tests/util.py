import os
import subprocess
from typing import Generator

os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

root_path = os.path.dirname(os.path.realpath(__file__))
inputs_path = os.path.join(root_path, "inputs")
output_path_reference = os.path.join(root_path, "output_reference")
output_path_betterproto = os.path.join(root_path, "output_betterproto")

if os.name == "nt":
    plugin_path = os.path.join(root_path, "..", "plugin.bat")
else:
    plugin_path = os.path.join(root_path, "..", "plugin.py")


def get_files(path, end: str) -> Generator[str, None, None]:
    for r, dirs, files in os.walk(path):
        for filename in [f for f in files if f.endswith(end)]:
            yield os.path.join(r, filename)


def get_directories(path):
    for root, directories, files in os.walk(path):
        for directory in directories:
            yield directory


def relative(file: str, path: str):
    return os.path.join(os.path.dirname(file), path)


def read_relative(file: str, path: str):
    with open(relative(file, path)) as fh:
        return fh.read()


def protoc_plugin(path: str, output_dir: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        f"protoc --plugin=protoc-gen-custom={plugin_path} --custom_out={output_dir} --proto_path={path} {path}/*.proto",
        shell=True,
        check=True,
    )


def protoc_reference(path: str, output_dir: str):
    subprocess.run(
        f"protoc --python_out={output_dir} --proto_path={path} {path}/*.proto",
        shell=True,
    )


def get_test_case_json_data(test_case_name, json_file_name=None):
    test_data_file_name = json_file_name if json_file_name else f"{test_case_name}.json"
    test_data_file_path = os.path.join(inputs_path, test_case_name, test_data_file_name)

    if not os.path.exists(test_data_file_path):
        return None

    with open(test_data_file_path) as fh:
        return fh.read()
