#!/usr/bin/env python
import os  # isort: skip

os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"


import subprocess
import importlib
from typing import Generator, Tuple

from google.protobuf.json_format import Parse
from google.protobuf import symbol_database
from google.protobuf.descriptor_pool import DescriptorPool

root = os.path.dirname(os.path.realpath(__file__))


def get_files(end: str) -> Generator[Tuple[str, str], None, None]:
    for r, dirs, files in os.walk(root):
        for filename in [f for f in files if f.endswith(end)]:
            parts = os.path.splitext(filename)[0].split("-")
            yield [parts[0], os.path.join(r, filename)]


if __name__ == "__main__":
    os.chdir(root)

    for base, filename in get_files(".proto"):
        subprocess.run(
            f"protoc --python_out=. {os.path.basename(filename)}", shell=True
        )
        subprocess.run(
            f"protoc --plugin=protoc-gen-custom=../../protoc-gen-betterpy.py --custom_out=. {os.path.basename(filename)}",
            shell=True,
        )

    for base, filename in get_files(".json"):
        # Reset the internal symbol database so we can import the `Test` message
        # multiple times. Ugh.
        sym = symbol_database.Default()
        sym.pool = DescriptorPool()
        imported = importlib.import_module(f"{base}_pb2")
        out = filename.replace(".json", ".bin")
        serialized = Parse(open(filename).read(), imported.Test()).SerializeToString()
        open(out, "wb").write(serialized)
