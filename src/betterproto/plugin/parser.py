import itertools
import os.path
import pathlib
import sys
from typing import List, Iterator

try:
    # betterproto[compiler] specific dependencies
    import black
    from google.protobuf.compiler import plugin_pb2 as plugin
    from google.protobuf.descriptor_pb2 import (
        DescriptorProto,
        EnumDescriptorProto,
        FieldDescriptorProto,
        ServiceDescriptorProto,
    )
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

from betterproto.plugin.models import (
    PluginRequestCompiler,
    OutputTemplate,
    MessageCompiler,
    FieldCompiler,
    OneOfFieldCompiler,
    MapEntryCompiler,
    EnumDefinitionCompiler,
    ServiceCompiler,
    ServiceMethodCompiler,
    is_map,
    is_oneof,
)


def traverse(proto_file: FieldDescriptorProto) -> Iterator:
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


def generate_code(
    request: plugin.CodeGeneratorRequest, response: plugin.CodeGeneratorResponse
) -> None:
    plugin_options = request.parameter.split(",") if request.parameter else []

    templates_folder = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "templates")
    )

    env = jinja2.Environment(
        trim_blocks=True,
        lstrip_blocks=True,
        loader=jinja2.FileSystemLoader(templates_folder),
    )
    template = env.get_template("template.py.j2")
    request_data = PluginRequestCompiler(plugin_request_obj=request)
    # Gather output packages
    for proto_file in request.proto_file:
        if (
            proto_file.package == "google.protobuf"
            and "INCLUDE_GOOGLE" not in plugin_options
        ):
            # If not INCLUDE_GOOGLE,
            # skip re-compiling Google's well-known types
            continue

        output_package_name = proto_file.package
        if output_package_name not in request_data.output_packages:
            # Create a new output if there is no output for this package
            request_data.output_packages[output_package_name] = OutputTemplate(
                parent_request=request_data, package_proto_obj=proto_file
            )
        # Add this input file to the output corresponding to this package
        request_data.output_packages[output_package_name].input_files.append(proto_file)

    # Read Messages and Enums
    # We need to read Messages before Services in so that we can
    # get the references to input/output messages for each service
    for output_package_name, output_package in request_data.output_packages.items():
        for proto_input_file in output_package.input_files:
            for item, path in traverse(proto_input_file):
                read_protobuf_type(item=item, path=path, output_package=output_package)

    # Read Services
    for output_package_name, output_package in request_data.output_packages.items():
        for proto_input_file in output_package.input_files:
            for index, service in enumerate(proto_input_file.service):
                read_protobuf_service(service, index, output_package)

    # Generate output files
    output_paths: pathlib.Path = set()
    for output_package_name, template_data in request_data.output_packages.items():

        # Add files to the response object
        output_path = pathlib.Path(*output_package_name.split("."), "__init__.py")
        output_paths.add(output_path)

        f: response.File = response.file.add()
        f.name: str = str(output_path)

        # Render and then format the output file
        f.content: str = black.format_str(
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


def read_protobuf_type(
    item: DescriptorProto, path: List[int], output_package: OutputTemplate
) -> None:
    if isinstance(item, DescriptorProto):
        if item.options.map_entry:
            # Skip generated map entry messages since we just use dicts
            return
        # Process Message
        message_data = MessageCompiler(parent=output_package, proto_obj=item, path=path)
        for index, field in enumerate(item.field):
            if is_map(field, item):
                MapEntryCompiler(
                    parent=message_data, proto_obj=field, path=path + [2, index]
                )
            elif is_oneof(field):
                OneOfFieldCompiler(
                    parent=message_data, proto_obj=field, path=path + [2, index]
                )
            else:
                FieldCompiler(
                    parent=message_data, proto_obj=field, path=path + [2, index]
                )
    elif isinstance(item, EnumDescriptorProto):
        # Enum
        EnumDefinitionCompiler(parent=output_package, proto_obj=item, path=path)


def read_protobuf_service(
    service: ServiceDescriptorProto, index: int, output_package: OutputTemplate
) -> None:
    service_data = ServiceCompiler(
        parent=output_package, proto_obj=service, path=[6, index],
    )
    for j, method in enumerate(service.method):
        ServiceMethodCompiler(
            parent=service_data, proto_obj=method, path=[6, index, 2, j],
        )
