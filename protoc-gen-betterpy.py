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
    FieldDescriptorProto,
)

from google.protobuf.compiler import plugin_pb2 as plugin


from jinja2 import Environment, PackageLoader


def py_type(
    package: str,
    imports: set,
    message: DescriptorProto,
    descriptor: FieldDescriptorProto,
) -> str:
    if descriptor.type in [1, 2, 6, 7, 15, 16]:
        return "float"
    elif descriptor.type in [3, 4, 5, 13, 17, 18]:
        return "int"
    elif descriptor.type == 8:
        return "bool"
    elif descriptor.type == 9:
        return "str"
    elif descriptor.type in [11, 14]:
        # Type referencing another defined Message or a named enum
        message_type = descriptor.type_name.lstrip(".")
        if message_type.startswith(package):
            # This is the current package, which has nested types flattened.
            message_type = message_type.lstrip(package).lstrip(".").replace(".", "")

        if "." in message_type:
            # This is imported from another package. No need
            # to use a forward ref and we need to add the import.
            message_type = message_type.strip('"')
            parts = message_type.split(".")
            imports.add(f"from .{'.'.join(parts[:-2])} import {parts[-2]}")
            message_type = f"{parts[-2]}.{parts[-1]}"

        # print(
        #     descriptor.name,
        #     package,
        #     descriptor.type_name,
        #     message_type,
        #     file=sys.stderr,
        # )

        return f'"{message_type}"'
    elif descriptor.type == 12:
        return "bytes"
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
                        # Adjust the name since we flatten the heirarchy.
                        n.name = item.name + n.name
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
                    lines[0] = lines[0].strip('"')
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

    # TODO: Refactor below to generate a single file per package if packages
    # are being used, otherwise one output for each input. Figure out how to
    # set up relative imports when needed and change the Message type refs to
    # use the import names when not in the current module.
    output_map = {}
    for proto_file in request.proto_file:
        out = proto_file.package
        if not out:
            out = os.path.splitext(proto_file.name)[0].replace(os.path.sep, ".")

        if out not in output_map:
            output_map[out] = {"package": proto_file.package, "files": []}
        output_map[out]["files"].append(proto_file)

    # TODO: Figure out how to handle gRPC request/response messages and add
    # processing below for Service.

    for filename, options in output_map.items():
        package = options["package"]
        # print(package, filename, file=sys.stderr)
        output = {"package": package, "imports": set(), "messages": [], "enums": []}

        for proto_file in options["files"]:
            # print(proto_file.message_type, file=sys.stderr)
            # print(proto_file.service, file=sys.stderr)
            # print(proto_file.source_code_info, file=sys.stderr)

            for item, path in traverse(proto_file):
                # print(item, file=sys.stderr)
                # print(path, file=sys.stderr)
                data = {"name": item.name}

                if isinstance(item, DescriptorProto):
                    # print(item, file=sys.stderr)
                    if item.options.map_entry:
                        # Skip generated map entry messages since we just use dicts
                        continue

                    data.update(
                        {
                            "type": "Message",
                            "comment": get_comment(proto_file, path),
                            "properties": [],
                        }
                    )

                    for i, f in enumerate(item.field):
                        t = py_type(package, output["imports"], item, f)

                        repeated = False
                        packed = False

                        field_type = f.Type.Name(f.type).lower()[5:]
                        map_types = None
                        if f.type == 11:
                            # This might be a map...
                            message_type = f.type_name.split(".").pop()
                            map_entry = f"{f.name.capitalize()}Entry"

                            if message_type == map_entry:
                                for nested in item.nested_type:
                                    if nested.name == map_entry:
                                        if nested.options.map_entry:
                                            # print("Found a map!", file=sys.stderr)
                                            k = py_type(
                                                package,
                                                output["imports"],
                                                item,
                                                nested.field[0],
                                            )
                                            v = py_type(
                                                package,
                                                output["imports"],
                                                item,
                                                nested.field[1],
                                            )
                                            t = f"Dict[{k}, {v}]"
                                            field_type = "map"
                                            map_types = (
                                                f.Type.Name(nested.field[0].type),
                                                f.Type.Name(nested.field[1].type),
                                            )

                        if f.label == 3 and field_type != "map":
                            # Repeated field
                            repeated = True
                            t = f"List[{t}]"

                            if f.type in [1, 2, 3, 4, 5, 6, 7, 8, 13, 15, 16, 17, 18]:
                                packed = True

                        data["properties"].append(
                            {
                                "name": f.name,
                                "number": f.number,
                                "comment": get_comment(proto_file, path + [2, i]),
                                "proto_type": int(f.type),
                                "field_type": field_type,
                                "map_types": map_types,
                                "type": t,
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

        output["imports"] = sorted(output["imports"])

        # Fill response
        f = response.file.add()
        # print(filename, file=sys.stderr)
        f.name = filename + ".py"
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
