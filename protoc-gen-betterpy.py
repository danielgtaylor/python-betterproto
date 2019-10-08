#!/usr/bin/env python

import sys

import itertools
import json
import os.path
from typing import Tuple, Any, List
import textwrap

from google.protobuf.descriptor_pb2 import (
    DescriptorProto,
    EnumDescriptorProto,
    FileDescriptorProto,
)

from google.protobuf.compiler import plugin_pb2 as plugin


from jinja2 import Environment, PackageLoader


def py_type(descriptor: DescriptorProto) -> Tuple[str, str]:
    if descriptor.type in [1, 2, 6, 7, 15, 16]:
        return "float", descriptor.default_value
    elif descriptor.type in [3, 4, 5, 13, 17, 18]:
        return "int", descriptor.default_value
    elif descriptor.type == 8:
        return "bool", descriptor.default_value.capitalize()
    elif descriptor.type == 9:
        default = ""
        if descriptor.default_value:
            default = f'"{descriptor.default_value}"'
        return "str", default
    elif descriptor.type == 11:
        # Type referencing another defined Message
        # print(descriptor.type_name, file=sys.stderr)
        # message_type = descriptor.type_name.replace(".", "")
        message_type = descriptor.type_name.split(".").pop()
        return f'"{message_type}"', f"lambda: {message_type}()"
    elif descriptor.type == 12:
        default = ""
        if descriptor.default_value:
            default = f'b"{descriptor.default_value}"'
        return "bytes", default
    elif descriptor.type == 14:
        # print(descriptor.type_name, file=sys.stderr)
        return descriptor.type_name.split(".").pop(), 0
    else:
        raise NotImplementedError(f"Unknown type {descriptor.type}")


def traverse(proto_file):
    def _traverse(path, items):
        for i, item in enumerate(items):
            yield item, path + [i]

            if isinstance(item, DescriptorProto):
                for enum in item.enum_type:
                    yield enum, path + [i, 4]

                if item.nested_type:
                    for n, p in _traverse(path + [i, 3], item.nested_type):
                        yield n, p

    return itertools.chain(
        _traverse([5], proto_file.enum_type), _traverse([4], proto_file.message_type)
    )


def get_comment(proto_file, path: List[int]) -> str:
    for sci in proto_file.source_code_info.location:
        # print(list(sci.path), path, file=sys.stderr)
        if list(sci.path) == path and sci.leading_comments:
            lines = textwrap.wrap(
                sci.leading_comments.strip().replace("\n", ""), width=75
            )

            if path[-2] == 2:
                # This is a field
                return "    # " + "    # ".join(lines)
            else:
                # This is a class
                if len(lines) == 1 and len(lines[0]) < 70:
                    return f'    """{lines[0]}"""'
                else:
                    return f'    """\n{"    ".join(lines)}\n    """'

    return ""


def generate_code(request, response):
    env = Environment(
        trim_blocks=True,
        lstrip_blocks=True,
        loader=PackageLoader("betterproto", "templates"),
    )
    template = env.get_template("main.py")

    for proto_file in request.proto_file:
        # print(proto_file.message_type, file=sys.stderr)
        # print(proto_file.source_code_info, file=sys.stderr)
        output = {
            "package": proto_file.package,
            "filename": proto_file.name,
            "messages": [],
            "enums": [],
        }

        # Parse request
        for item, path in traverse(proto_file):
            # print(item, file=sys.stderr)
            # print(path, file=sys.stderr)
            data = {"name": item.name}

            if isinstance(item, DescriptorProto):
                # print(item, file=sys.stderr)
                data.update(
                    {
                        "type": "Message",
                        "comment": get_comment(proto_file, path),
                        "properties": [],
                    }
                )

                for i, f in enumerate(item.field):
                    t, zero = py_type(f)
                    repeated = False
                    packed = False

                    if f.label == 3:
                        # Repeated field
                        repeated = True
                        t = f"List[{t}]"
                        zero = "list"

                        if f.type in [1, 2, 3, 4, 5, 6, 7, 8, 13, 15, 16, 17, 18]:
                            packed = True

                    data["properties"].append(
                        {
                            "name": f.name,
                            "number": f.number,
                            "comment": get_comment(proto_file, path + [2, i]),
                            "proto_type": int(f.type),
                            "field_type": f.Type.Name(f.type).lower()[5:],
                            "type": t,
                            "zero": zero,
                            "repeated": repeated,
                            "packed": packed,
                        }
                    )
                    # print(f, file=sys.stderr)

                output["messages"].append(data)

            elif isinstance(item, EnumDescriptorProto):
                # print(item.name, path, file=sys.stderr)
                data.update(
                    {
                        "type": "Enum",
                        "comment": get_comment(proto_file, path),
                        "entries": [
                            {
                                "name": v.name,
                                "value": v.number,
                                "comment": get_comment(proto_file, path + [2, i]),
                            }
                            for i, v in enumerate(item.value)
                        ],
                    }
                )

                output["enums"].append(data)

        # Fill response
        f = response.file.add()
        f.name = os.path.splitext(proto_file.name)[0] + ".py"
        # f.content = json.dumps(output, indent=2)
        f.content = template.render(description=output).rstrip("\n") + "\n"


if __name__ == "__main__":
    # Read request message from stdin
    data = sys.stdin.buffer.read()

    # Parse request
    request = plugin.CodeGeneratorRequest()
    request.ParseFromString(data)

    # Create response
    response = plugin.CodeGeneratorResponse()

    # Generate code
    generate_code(request, response)

    # Serialise response message
    output = response.SerializeToString()

    # Write to stdout
    sys.stdout.buffer.write(output)
