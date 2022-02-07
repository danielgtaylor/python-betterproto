#!/usr/bin/env python

import itertools
import os.path
import sys
import textwrap
from collections import defaultdict
from typing import Dict, List, Optional, Type

try:
    import black
except ImportError:
    print(
        "Unable to import `black` formatter. Did you install the compiler feature with `pip install betterproto[compiler]`?"
    )
    raise SystemExit(1)

import jinja2
import stringcase

from google.protobuf.compiler import plugin_pb2 as plugin
from google.protobuf.descriptor_pb2 import (
    DescriptorProto,
    EnumDescriptorProto,
    FieldDescriptorProto,
)

from betterproto.casing import safe_snake_case

import google.protobuf.wrappers_pb2 as google_wrappers

WRAPPER_TYPES: Dict[str, Optional[Type]] = defaultdict(
    lambda: None,
    {
        "google.protobuf.DoubleValue": google_wrappers.DoubleValue,
        "google.protobuf.FloatValue": google_wrappers.FloatValue,
        "google.protobuf.Int64Value": google_wrappers.Int64Value,
        "google.protobuf.UInt64Value": google_wrappers.UInt64Value,
        "google.protobuf.Int32Value": google_wrappers.Int32Value,
        "google.protobuf.UInt32Value": google_wrappers.UInt32Value,
        "google.protobuf.BoolValue": google_wrappers.BoolValue,
        "google.protobuf.StringValue": google_wrappers.StringValue,
        "google.protobuf.BytesValue": google_wrappers.BytesValue,
    },
)


def _get_proto(request, name: str):
    return next(f for f in request.proto_file if f.name == name)


def get_ref_type(
    package: str, imports: set, type_name: str, unwrap: bool = True
) -> str:
    """
    Return a Python type name for a proto type reference. Adds the import if
    necessary. Unwraps well known type if required.
    """

    #    print("get reference type package: " + package + " type: " + type_name + " " + str(unwrap), file=sys.stderr)

    # If the package name is a blank string, then this should still work
    # because by convention packages are lowercase and message/enum types are
    # pascal-cased. May require refactoring in the future.
    type_name = type_name.lstrip(".")

    # Check if type is wrapper.
    wrapper_class = WRAPPER_TYPES[type_name]

    if unwrap:

        if wrapper_class:
            wrapped_type = type(wrapper_class().value)
            return f"Optional[{wrapped_type.__name__}]"

        if type_name == "google.protobuf.Duration":
            return "timedelta"

        if type_name == "google.protobuf.Timestamp":
            return "datetime"

    elif wrapper_class:
        imports.add(f"from {wrapper_class.__module__} import {wrapper_class.__name__}")
        return f"{wrapper_class.__name__}"

    if type_name.startswith(package):
        parts = type_name.lstrip(package).lstrip(".").split(".")
        if len(parts) == 1 or (len(parts) > 1 and parts[0][0] == parts[0][0].upper()):
            # This is the current package, which has nested types flattened.
            # foo.bar_thing => FooBarThing
            cased = [stringcase.pascalcase(part) for part in parts]
            type_name = f'"{"".join(cased)}"'

    if type_name == "google.protobuf.Empty":
        imports.add(f"from google.protobuf.empty_pb2 import Empty")

    if "." in type_name:
        # This is imported from another package. No need
        # to use a forward ref and we need to add the import.
        parts = type_name.split(".")
        parts[-1] = stringcase.pascalcase(parts[-1])
        type_name = (
            f"{parts[-1]}"
        )  # type without namespace should by imported by user in proto file

    return type_name


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
        #        print("py type: " + package + " type: " + str(descriptor), file=sys.stderr)
        return get_ref_type(package, imports, descriptor.type_name)
    elif descriptor.type == 12:
        return "bytes"
    else:
        raise NotImplementedError(f"Unknown type {descriptor.type}")


def get_py_zero(type_num: int) -> str:
    zero = 0
    if type_num in []:
        zero = 0.0
    elif type_num == 8:
        zero = "False"
    elif type_num == 9:
        zero = '""'
    elif type_num == 11:
        zero = "None"
    elif type_num == 12:
        zero = 'b""'

    return zero


def traverse(proto_file):
    def _traverse(path, items, prefix=""):
        for i, item in enumerate(items):
            # Adjust the name since we flatten the heirarchy.
            item.name = next_prefix = prefix + item.name
            yield item, path + [i]

            if isinstance(item, DescriptorProto):
                for enum in item.enum_type:
                    enum.name = next_prefix + enum.name
                    yield enum, path + [i, 4]

                if item.nested_type:
                    for n, p in _traverse(path + [i, 3], item.nested_type, next_prefix):
                        yield n, p

    return itertools.chain(
        _traverse([5], proto_file.enum_type), _traverse([4], proto_file.message_type)
    )


def get_comment(proto_file, path: List[int], indent: int = 4) -> str:
    pad = " " * indent
    for sci in proto_file.source_code_info.location:
        # print(list(sci.path), path, file=sys.stderr)
        if list(sci.path) == path and sci.leading_comments:
            lines = textwrap.wrap(
                sci.leading_comments.strip().replace("\n", ""), width=79 - indent
            )

            if path[-2] == 2 and path[-4] != 6:
                # This is a field
                return f"{pad}# " + f"\n{pad}# ".join(lines)
            else:
                # This is a message, enum, service, or method
                if len(lines) == 1 and len(lines[0]) < 79 - indent - 6:
                    lines[0] = lines[0].strip('"')
                    return f'{pad}"""{lines[0]}"""'
                else:
                    joined = f"\n{pad}".join(lines)
                    return f'{pad}"""\n{pad}{joined}\n{pad}"""'

    return ""


def get_message(input_type, description):

    for msg in description["messages"]:
        #        print("  - " + msg["name"], file=sys.stderr)
        if msg["name"] == input_type:
            #            print("  + found", file=sys.stderr)
            return msg

    return None


def source_model(model, dependecies=None):

    outputs = {}

    # TODO: Figure out how to handle gRPC request/response messages and add
    # processing below for Service.

    for filename, options in model.items():

        if filename in outputs:
            continue

        package = options["package"]

        outputs[filename] = {
            "package": package,
            "files": [f.name for f in options["files"]],
            "imports": options["imports"],
            "datetime_imports": set(),
            "typing_imports": set(),
            "messages": [],
            "enums": [],
            "services": [],
        }

        type_mapping = {}

        for proto_file in options["files"]:
            #            print(proto_file.message_type, file=sys.stderr)
            #            print(proto_file.service, file=sys.stderr)
            #            print(proto_file.source_code_info, file=sys.stderr)

            for item, path in traverse(proto_file):
                #                print(item, file=sys.stderr)
                #                print(path, file=sys.stderr)
                data = {"name": item.name, "py_name": stringcase.pascalcase(item.name)}

                #                print(" type data " + str(data), file=sys.stderr)

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
                        t = py_type(package, outputs[filename]["imports"], item, f)
                        zero = get_py_zero(f.type)

                        repeated = False
                        packed = False

                        field_type = f.Type.Name(f.type).lower()[5:]

                        field_wraps = ""
                        if f.type_name.startswith(
                            ".google.protobuf"
                        ) and f.type_name.endswith("Value"):
                            w = f.type_name.split(".").pop()[:-5].upper()
                            field_wraps = f"betterproto.TYPE_{w}"

                        map_types = None
                        if f.type == 11:
                            # This might be a map...
                            message_type = f.type_name.split(".").pop().lower()
                            # message_type = py_type(package)
                            map_entry = f"{f.name.replace('_', '').lower()}entry"

                            if message_type == map_entry:
                                for nested in item.nested_type:
                                    if (
                                        nested.name.replace("_", "").lower()
                                        == map_entry
                                    ):
                                        if nested.options.map_entry:
                                            # print("Found a map!", file=sys.stderr)
                                            k = py_type(
                                                package,
                                                outputs[filename]["imports"],
                                                item,
                                                nested.field[0],
                                            )
                                            v = py_type(
                                                package,
                                                outputs[filename]["imports"],
                                                item,
                                                nested.field[1],
                                            )
                                            t = f"Dict[{k}, {v}]"
                                            field_type = "map"
                                            map_types = (
                                                f.Type.Name(nested.field[0].type),
                                                f.Type.Name(nested.field[1].type),
                                            )
                                            outputs[filename]["typing_imports"].add(
                                                "Dict"
                                            )

                        if f.label == 3 and field_type != "map":
                            # Repeated field
                            repeated = True
                            t = f"List[{t}]"
                            zero = "[]"
                            outputs[filename]["typing_imports"].add("List")

                            if f.type in [1, 2, 3, 4, 5, 6, 7, 8, 13, 15, 16, 17, 18]:
                                packed = True

                        one_of = ""
                        if f.HasField("oneof_index"):
                            one_of = item.oneof_decl[f.oneof_index].name

                        if "Optional[" in t:
                            outputs[filename]["typing_imports"].add("Optional")

                        if "timedelta" in t:
                            outputs[filename]["datetime_imports"].add("timedelta")
                        elif "datetime" in t:
                            outputs[filename]["datetime_imports"].add("datetime")

                        data["properties"].append(
                            {
                                "name": f.name,
                                "py_name": safe_snake_case(f.name),
                                "number": f.number,
                                "comment": get_comment(proto_file, path + [2, i]),
                                "proto_type": int(f.type),
                                "field_type": field_type,
                                "field_wraps": field_wraps,
                                "map_types": map_types,
                                "type": t,
                                "zero": zero,
                                "repeated": repeated,
                                "packed": packed,
                                "one_of": one_of,
                            }
                        )
                        # print(f, file=sys.stderr)

                    outputs[filename]["messages"].append(data)
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

                    outputs[filename]["enums"].append(data)

            for i, service in enumerate(proto_file.service):
                # print(service, file=sys.stderr)

                data = {
                    "name": service.name,
                    "py_name": stringcase.pascalcase(service.name),
                    "comment": get_comment(proto_file, [6, i]),
                    "methods": [],
                }

                for j, method in enumerate(service.method):
                    if method.client_streaming:
                        raise NotImplementedError("Client streaming not yet supported")

                    input_message = None
                    input_type = get_ref_type(
                        package, outputs[filename]["imports"], method.input_type
                    ).strip('"')

                    input_message = get_message(input_type, outputs[filename])

                    #                    if not input_message:
                    #                        print(" * " + input_type + " not found in the current namespace and " + filename, file=sys.stderr)

                    if (
                        dependecies and not input_message
                    ):  # iterate over dependecies and try to find model for dependet typs inside
                        for f, desc in dependecies.items():
                            #                            print(" looking for " + input_type + " in " + f, file=sys.stderr)
                            input_message = get_message(input_type, desc)

                            if input_message:
                                break

                    if input_message:
                        for field in input_message["properties"]:
                            if field["zero"] == "None":
                                outputs[filename]["typing_imports"].add("Optional")

                    data["methods"].append(
                        {
                            "name": method.name,
                            "py_name": stringcase.snakecase(method.name),
                            "comment": get_comment(proto_file, [6, i, 2, j], indent=8),
                            "route": f"/{package}.{service.name}/{method.name}",
                            "input": get_ref_type(
                                package, outputs[filename]["imports"], method.input_type
                            ).strip('"'),
                            "input_message": input_message,
                            "output": get_ref_type(
                                package,
                                outputs[filename]["imports"],
                                method.output_type,
                                unwrap=False,
                            ).strip('"'),
                            "client_streaming": method.client_streaming,
                            "server_streaming": method.server_streaming,
                        }
                    )

                    if method.server_streaming:
                        outputs[filename]["typing_imports"].add("AsyncGenerator")

                outputs[filename]["services"].append(data)

        outputs[filename]["imports"] = sorted(outputs[filename]["imports"])
        outputs[filename]["datetime_imports"] = sorted(
            outputs[filename]["datetime_imports"]
        )
        outputs[filename]["typing_imports"] = sorted(
            outputs[filename]["typing_imports"]
        )

    return outputs


def generate_code(request, response):
    env = jinja2.Environment(
        trim_blocks=True,
        lstrip_blocks=True,
        loader=jinja2.FileSystemLoader("%s/templates/" % os.path.dirname(__file__)),
    )
    template = env.get_template("template.py.j2")

    # iterate over requested files to generate, not over all dependecies (dependecies are generated by external tool)
    for file_to_generate in request.file_to_generate:

        #        print("===========================================", file=sys.stderr)
        #        print("generate request " + file_to_generate, file=sys.stderr)

        # similar to original grpc, find descriptor for file we are generating
        proto_file = _get_proto(request, file_to_generate)

        output_map = {}
        dependecy_map = {}

        # go over imports and add all imports implicitly
        imports = set()
        for dep in list(proto_file.dependency):

            imported_proto_file = _get_proto(request, dep)

            if imported_proto_file.package.startswith("google"):
                continue

            path, filename = os.path.split(imported_proto_file.name)
            file_name = os.path.splitext(filename)[0]

            import_path = imported_proto_file.package

            if path:
                import_path += "." + path.replace(os.path.sep, ".")

            imports.add("from " + import_path + "." + file_name + " import *")
            import_dependecy = imported_proto_file.package + "." + file_name

            if import_dependecy not in dependecy_map:
                dependecy_map[import_dependecy] = {
                    "package": imported_proto_file.package,
                    "files": [],
                    "imports": [],
                }

            dependecy_map[import_dependecy]["files"].append(imported_proto_file)

        out = proto_file.package + "." + proto_file.name.rsplit(".", 1)[0]

        if out.startswith("google"):
            continue

        if not out:
            out = os.path.splitext(proto_file.name)[0].replace(os.path.sep, ".")

        if out not in output_map:
            output_map[out] = {
                "package": proto_file.package,
                "files": [],
                "imports": imports,
            }

        output_map[out]["files"].append(proto_file)

    deps = source_model(dependecy_map)

    for filename, description in source_model(output_map, deps).items():

        # Fill response
        f = response.file.add()
        # print(filename, file=sys.stderr)
        f.name = filename.replace(".", os.path.sep) + ".py"

        # Render and then format the output file.
        f.content = black.format_str(
            template.render(description=description),
            mode=black.FileMode(target_versions=set([black.TargetVersion.PY37])),
        )

    inits = set([""])
    for f in response.file:
        # Ensure output paths exist
        # print(f.name, file=sys.stderr)
        dirnames = os.path.dirname(f.name)
        if dirnames:
            os.makedirs(dirnames, exist_ok=True)
            base = ""
            for part in dirnames.split(os.path.sep):
                base = os.path.join(base, part)
                inits.add(base)

    for base in inits:
        name = os.path.join(base, "__init__.py")

        if os.path.exists(name):
            # Never overwrite inits as they may have custom stuff in them.
            continue

        init = response.file.add()
        init.name = name
        init.content = b""

    filenames = sorted([f.name for f in response.file])


def main():
    """The plugin's main entry point."""
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


if __name__ == "__main__":
    main()
