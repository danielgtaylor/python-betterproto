#!/usr/bin/env python
import collections
import itertools
import os.path
import pathlib
import sys
import textwrap
from typing import List, Union


from betterproto.lib.google.protobuf import ServiceDescriptorProto
from betterproto.compile.importing import get_type_reference

try:
    # betterproto[compiler] specific dependencies
    import black
    from google.protobuf.compiler import plugin_pb2 as plugin
    from google.protobuf.descriptor_pb2 import (
        DescriptorProto,
        EnumDescriptorProto,
        FieldDescriptorProto,
    )
    from google.protobuf.compiler.plugin_pb2 import CodeGeneratorRequest
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

from .plugin_dataclasses import (
    OutputTemplate,
    ProtoInputFile,
    Message,
    Field,
    OneOfField,
    MapField,
    EnumDefinition,
    Service,
    ServiceMethod,
    is_map,
    is_oneof
)


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
        template_data = OutputTemplate(input_package=output_package_content["input_package"])
        for input_proto_file in output_package_content["files"]:
            ProtoInputFile(parent=template_data, proto_obj=input_proto_file)
        output_package_content["template_data"] = template_data

    # Read Messages and Enums
    for output_package_name, output_package_content in output_package_files.items():
        for proto_file_data in output_package_content["template_data"].input_files:
            for item, path in traverse(proto_file_data.proto_obj):
                read_protobuf_type(item=item, path=path, proto_file_data=proto_file_data)

    # Read Services
    for output_package_name, output_package_content in output_package_files.items():
        for proto_file_data in output_package_content["template_data"].input_files:
            for index, service in enumerate(proto_file_data.proto_obj.service):
                read_protobuf_service(service, index, proto_file_data)

    # Render files
    output_paths = set()
    for output_package_name, output_package_content in output_package_files.items():
        template_data = output_package_content["template_data"]

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


def read_protobuf_type(item: DescriptorProto, path: List[int], proto_file_data: ProtoInputFile):
    if isinstance(item, DescriptorProto):
        if item.options.map_entry:
            # Skip generated map entry messages since we just use dicts
            return
        # Process Message
        message_data = Message(
            parent=proto_file_data,
            proto_obj=item,
            path=path
        )
        for index, field in enumerate(item.field):
            if is_map(field, item):
                MapField(parent=message_data, proto_obj=field, path=path+[2, index])
            elif is_oneof(field):
                OneOfField(parent=message_data, proto_obj=field, path=path+[2, index])
            else:
                Field(parent=message_data, proto_obj=field, path=path+[2, index])
    elif isinstance(item, EnumDescriptorProto):
        # Enum
        EnumDefinition(proto_obj=item, parent=proto_file_data, path=path)


def read_protobuf_service(service: ServiceDescriptorProto, index: int, proto_file_data: ProtoInputFile):
    service_data = Service(
        parent=proto_file_data,
        proto_obj=service,
        path=[6, index],
    )
    for j, method in enumerate(service.method):

        ServiceMethod(
            parent=service_data,
            proto_obj=method,
            path=[6, index, 2, j],
        )


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
