#!/usr/bin/env python
import collections
import itertools
import os.path
import pathlib
import re
import sys
import textwrap
from typing import List, Union

from google.protobuf.compiler.plugin_pb2 import CodeGeneratorRequest

import betterproto
from betterproto.compile.importing import get_type_reference, parse_source_type_name
from betterproto.compile.naming import (
    pythonize_class_name,
    pythonize_field_name,
    pythonize_method_name,
)
from betterproto.lib.google.protobuf import ServiceDescriptorProto

try:
    # betterproto[compiler] specific dependencies
    import black
    from google.protobuf.compiler import plugin_pb2 as plugin
    from google.protobuf.descriptor_pb2 import (
        DescriptorProto,
        EnumDescriptorProto,
        FieldDescriptorProto,
    )
    import google.protobuf.wrappers_pb2 as google_wrappers
    import jinja2
except ImportError as err:
    missing_import = err.args[0][17:-1]
    print(
        "\033[31m"
        f"Unable to import `{missing_import}` from betterproto plugin! "
        "Please ensure that you've installed betterproto as "
        '`pip install "betterproto[compiler]"` so that compiler dependencies '
        "are included."
        "\033[0m"
    )
    raise SystemExit(1)


def py_type(package: str, imports: set, field: FieldDescriptorProto) -> str:
    if field.type in [1, 2]:
        return "float"
    elif field.type in [3, 4, 5, 6, 7, 13, 15, 16, 17, 18]:
        return "int"
    elif field.type == 8:
        return "bool"
    elif field.type == 9:
        return "str"
    elif field.type in [11, 14]:
        # Type referencing another defined Message or a named enum
        return get_type_reference(package, imports, field.type_name)
    elif field.type == 12:
        return "bytes"
    else:
        raise NotImplementedError(f"Unknown type {field.type}")


def get_py_zero(type_num: int) -> Union[str, float]:
    zero: Union[str, float] = 0
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
    # Todo: Keep information about nested hierarchy
    def _traverse(path, items, prefix=""):
        for i, item in enumerate(items):
            # Adjust the name since we flatten the hierarchy.
            # Todo: don't change the name, but include full name in returned tuple
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


def generate_code(request, response):
    plugin_options = request.parameter.split(",") if request.parameter else []

    env = jinja2.Environment(
        trim_blocks=True,
        lstrip_blocks=True,
        loader=jinja2.FileSystemLoader("%s/templates/" % os.path.dirname(__file__)),
    )
    template = env.get_template("template.py.j2")

    # Gather output packages
    output_package_files = collections.defaultdict()
    for proto_file in request.proto_file:
        if (
            proto_file.package == "google.protobuf"
            and "INCLUDE_GOOGLE" not in plugin_options
        ):
            continue

        output_package = proto_file.package
        output_package_files.setdefault(
            output_package, {"input_package": proto_file.package, "files": []}
        )
        output_package_files[output_package]["files"].append(proto_file)

    # Initialize Template data for each package
    for output_package_name, output_package_content in output_package_files.items():
        template_data = {
            "input_package": output_package_content["input_package"],
            "files": [f.name for f in output_package_content["files"]],
            "imports": set(),
            "datetime_imports": set(),
            "typing_imports": set(),
            "messages": [],
            "enums": [],
            "services": [],
        }
        output_package_content["template_data"] = template_data

    # Read Messages and Enums
    output_types = []
    for output_package_name, output_package_content in output_package_files.items():
        for proto_file in output_package_content["files"]:
            for item, path in traverse(proto_file):
                type_data = read_protobuf_type(
                    item, path, proto_file, output_package_content
                )
                output_types.append(type_data)

    # Read Services
    for output_package_name, output_package_content in output_package_files.items():
        for proto_file in output_package_content["files"]:
            for index, service in enumerate(proto_file.service):
                read_protobuf_service(
                    service, index, proto_file, output_package_content, output_types
                )

    # Render files
    output_paths = set()
    for output_package_name, output_package_content in output_package_files.items():
        template_data = output_package_content["template_data"]
        template_data["imports"] = sorted(template_data["imports"])
        template_data["datetime_imports"] = sorted(template_data["datetime_imports"])
        template_data["typing_imports"] = sorted(template_data["typing_imports"])

        # Fill response
        output_path = pathlib.Path(*output_package_name.split("."), "__init__.py")
        output_paths.add(output_path)

        f = response.file.add()
        f.name = str(output_path)

        # Render and then format the output file.
        f.content = black.format_str(
            template.render(description=template_data),
            mode=black.FileMode(target_versions={black.TargetVersion.PY37}),
        )

    # Make each output directory a package with __init__ file
    init_files = (
        set(
            directory.joinpath("__init__.py")
            for path in output_paths
            for directory in path.parents
        )
        - output_paths
    )

    for init_file in init_files:
        init = response.file.add()
        init.name = str(init_file)

    for output_package_name in sorted(output_paths.union(init_files)):
        print(f"Writing {output_package_name}", file=sys.stderr)


def read_protobuf_type(item: DescriptorProto, path: List[int], proto_file, content):
    input_package_name = content["input_package"]
    template_data = content["template_data"]
    data = {
        "name": item.name,
        "py_name": pythonize_class_name(item.name),
        "descriptor": item,
        "package": input_package_name,
    }
    if isinstance(item, DescriptorProto):
        # print(item, file=sys.stderr)
        if item.options.map_entry:
            # Skip generated map entry messages since we just use dicts
            return

        data.update(
            {
                "type": "Message",
                "comment": get_comment(proto_file, path),
                "properties": [],
            }
        )

        for i, f in enumerate(item.field):
            t = py_type(input_package_name, template_data["imports"], f)
            zero = get_py_zero(f.type)

            repeated = False
            packed = False

            field_type = f.Type.Name(f.type).lower()[5:]

            field_wraps = ""
            match_wrapper = re.match(r"\.google\.protobuf\.(.+)Value", f.type_name)
            if match_wrapper:
                wrapped_type = "TYPE_" + match_wrapper.group(1).upper()
                if hasattr(betterproto, wrapped_type):
                    field_wraps = f"betterproto.{wrapped_type}"

            map_types = None
            if f.type == 11:
                # This might be a map...
                message_type = f.type_name.split(".").pop().lower()
                # message_type = py_type(package)
                map_entry = f"{f.name.replace('_', '').lower()}entry"

                if message_type == map_entry:
                    for nested in item.nested_type:
                        if nested.name.replace("_", "").lower() == map_entry:
                            if nested.options.map_entry:
                                # print("Found a map!", file=sys.stderr)
                                k = py_type(
                                    input_package_name,
                                    template_data["imports"],
                                    nested.field[0],
                                )
                                v = py_type(
                                    input_package_name,
                                    template_data["imports"],
                                    nested.field[1],
                                )
                                t = f"Dict[{k}, {v}]"
                                field_type = "map"
                                map_types = (
                                    f.Type.Name(nested.field[0].type),
                                    f.Type.Name(nested.field[1].type),
                                )
                                template_data["typing_imports"].add("Dict")

            if f.label == 3 and field_type != "map":
                # Repeated field
                repeated = True
                t = f"List[{t}]"
                zero = "[]"
                template_data["typing_imports"].add("List")

                if f.type in [1, 2, 3, 4, 5, 6, 7, 8, 13, 15, 16, 17, 18]:
                    packed = True

            one_of = ""
            if f.HasField("oneof_index"):
                one_of = item.oneof_decl[f.oneof_index].name

            if "Optional[" in t:
                template_data["typing_imports"].add("Optional")

            if "timedelta" in t:
                template_data["datetime_imports"].add("timedelta")
            elif "datetime" in t:
                template_data["datetime_imports"].add("datetime")

            data["properties"].append(
                {
                    "name": f.name,
                    "py_name": pythonize_field_name(f.name),
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

        template_data["messages"].append(data)
        return data
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

        template_data["enums"].append(data)
        return data


def lookup_method_input_type(method, types):
    package, name = parse_source_type_name(method.input_type)

    for known_type in types:
        if known_type["type"] != "Message":
            continue

        # Nested types are currently flattened without dots.
        # Todo: keep a fully quantified name in types, that is comparable with method.input_type
        if (
            package == known_type["package"]
            and name.replace(".", "") == known_type["name"]
        ):
            return known_type


def is_mutable_field_type(field_type: str) -> bool:
    return field_type.startswith("List[") or field_type.startswith("Dict[")


def read_protobuf_service(
    service: ServiceDescriptorProto, index, proto_file, content, output_types
):
    input_package_name = content["input_package"]
    template_data = content["template_data"]
    # print(service, file=sys.stderr)
    data = {
        "name": service.name,
        "py_name": pythonize_class_name(service.name),
        "comment": get_comment(proto_file, [6, index]),
        "methods": [],
    }
    for j, method in enumerate(service.method):
        method_input_message = lookup_method_input_type(method, output_types)

        # This section ensures that method arguments having a default
        # value that is initialised as a List/Dict (mutable) is replaced
        # with None and initialisation is deferred to the beginning of the
        # method definition. This is done so to avoid any side-effects.
        # Reference: https://docs.python-guide.org/writing/gotchas/#mutable-default-arguments
        mutable_default_args = []

        if method_input_message:
            for field in method_input_message["properties"]:
                if (
                    not method.client_streaming
                    and field["zero"] != "None"
                    and is_mutable_field_type(field["type"])
                ):
                    mutable_default_args.append((field["py_name"], field["zero"]))
                    field["zero"] = "None"

                if field["zero"] == "None":
                    template_data["typing_imports"].add("Optional")

        data["methods"].append(
            {
                "name": method.name,
                "py_name": pythonize_method_name(method.name),
                "comment": get_comment(proto_file, [6, index, 2, j], indent=8),
                "route": f"/{input_package_name}.{service.name}/{method.name}",
                "input": get_type_reference(
                    input_package_name, template_data["imports"], method.input_type
                ).strip('"'),
                "input_message": method_input_message,
                "output": get_type_reference(
                    input_package_name,
                    template_data["imports"],
                    method.output_type,
                    unwrap=False,
                ),
                "client_streaming": method.client_streaming,
                "server_streaming": method.server_streaming,
                "mutable_default_args": mutable_default_args,
            }
        )

        if method.client_streaming:
            template_data["typing_imports"].add("AsyncIterable")
            template_data["typing_imports"].add("Iterable")
            template_data["typing_imports"].add("Union")
        if method.server_streaming:
            template_data["typing_imports"].add("AsyncIterator")
    template_data["services"].append(data)


def main():
    """The plugin's main entry point."""
    # Read request message from stdin
    data = sys.stdin.buffer.read()

    # Parse request
    request = plugin.CodeGeneratorRequest()
    request.ParseFromString(data)

    dump_file = os.getenv("BETTERPROTO_DUMP")
    if dump_file:
        dump_request(dump_file, request)

    # Create response
    response = plugin.CodeGeneratorResponse()

    # Generate code
    generate_code(request, response)

    # Serialise response message
    output = response.SerializeToString()

    # Write to stdout
    sys.stdout.buffer.write(output)


def dump_request(dump_file: str, request: CodeGeneratorRequest):
    """
    For developers: Supports running plugin.py standalone so its possible to debug it.
    Run protoc (or generate.py) with BETTERPROTO_DUMP="yourfile.bin" to write the request to a file.
    Then run plugin.py from your IDE in debugging mode, and redirect stdin to the file.
    """
    with open(str(dump_file), "wb") as fh:
        sys.stderr.write(f"\033[31mWriting input from protoc to: {dump_file}\033[0m\n")
        fh.write(request.SerializeToString())


if __name__ == "__main__":
    main()
