import asyncio
import os
from pathlib import Path
from typing import Generator, IO, Optional

os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

root_path = Path(__file__).resolve().parent
inputs_path = root_path.joinpath("inputs")
output_path_reference = root_path.joinpath("output_reference")
output_path_betterproto = root_path.joinpath("output_betterproto")

if os.name == "nt":
    plugin_path = root_path.joinpath("..", "plugin.bat").resolve()
else:
    plugin_path = root_path.joinpath("..", "plugin.py").resolve()


def get_files(path, suffix: str) -> Generator[str, None, None]:
    for r, dirs, files in os.walk(path):
        for filename in [f for f in files if f.endswith(suffix)]:
            yield os.path.join(r, filename)


def get_directories(path):
    for root, directories, files in os.walk(path):
        for directory in directories:
            yield directory


async def protoc_plugin(path: str, output_dir: str):
    proc = await asyncio.create_subprocess_shell(
        f"protoc --plugin=protoc-gen-custom={plugin_path} --custom_out={output_dir} --proto_path={path} {path}/*.proto",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    return (*(await proc.communicate()), proc.returncode)


async def protoc_reference(path: str, output_dir: str):
    proc = await asyncio.create_subprocess_shell(
        f"protoc --python_out={output_dir} --proto_path={path} {path}/*.proto",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    return (*(await proc.communicate()), proc.returncode)


def get_test_case_json_data(test_case_name: str, json_file_name: Optional[str] = None):
    test_data_file_name = json_file_name if json_file_name else f"{test_case_name}.json"
    test_data_file_path = inputs_path.joinpath(test_case_name, test_data_file_name)

    if not test_data_file_path.exists():
        return None

    with test_data_file_path.open("r") as fh:
        return fh.read()
