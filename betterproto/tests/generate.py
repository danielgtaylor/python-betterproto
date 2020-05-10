#!/usr/bin/env python
import os

# Force pure-python implementation instead of C++, otherwise imports
# break things because we can't properly reset the symbol database.
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

import importlib
import json
import subprocess
import sys
from typing import Generator, Tuple

from google.protobuf import symbol_database
from google.protobuf.descriptor_pool import DescriptorPool
from google.protobuf.json_format import MessageToJson, Parse


root = os.path.dirname(os.path.realpath(__file__))


def get_files(end: str) -> Generator[str, None, None]:
    for r, dirs, files in os.walk(root):
        for filename in [f for f in files if f.endswith(end)]:
            yield os.path.join(r, filename)


def get_base(filename: str) -> str:
    return os.path.splitext(os.path.basename(filename))[0]


def ensure_ext(filename: str, ext: str) -> str:
    if not filename.endswith(ext):
        return filename + ext
    return filename


if __name__ == "__main__":
    os.chdir(root)

    if len(sys.argv) > 1:
        proto_files = [ensure_ext(f, ".proto") for f in sys.argv[1:]]
        bases = {get_base(f) for f in proto_files}
        json_files = [
            f for f in get_files(".json") if get_base(f).split("-")[0] in bases
        ]
    else:
        proto_files = get_files(".proto")
        json_files = get_files(".json")

    if os.name == 'nt':
        plugin_path = os.path.join('..', 'plugin.bat')
    else:
        plugin_path = os.path.join('..', 'plugin.py')
    

    for filename in proto_files:
        print(f"Generating code for {os.path.basename(filename)}")
        subprocess.run(
            f"protoc --python_out=. {os.path.basename(filename)}", shell=True
        )
        subprocess.run(
            f"protoc --plugin=protoc-gen-custom={plugin_path} --custom_out=. {os.path.basename(filename)}",
            shell=True,
        )

    for filename in json_files:
        # Reset the internal symbol database so we can import the `Test` message
        # multiple times. Ugh.
        sym = symbol_database.Default()
        sym.pool = DescriptorPool()

        parts = get_base(filename).split("-")
        out = filename.replace(".json", ".bin")
        print(f"Using {parts[0]}_pb2 to generate {os.path.basename(out)}")

        imported = importlib.import_module(f"{parts[0]}_pb2")
        input_json = open(filename).read()
        parsed = Parse(input_json, imported.Test())
        serialized = parsed.SerializeToString()
        preserve = "casing" not in filename
        serialized_json = MessageToJson(parsed, preserving_proto_field_name=preserve)

        s_loaded = json.loads(serialized_json)
        in_loaded = json.loads(input_json)

        if s_loaded != in_loaded:
            raise AssertionError("Expected JSON to be equal:", s_loaded, in_loaded)

        open(out, "wb").write(serialized)
