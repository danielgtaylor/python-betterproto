from betterproto.lib.google.protobuf import (
    DescriptorProto,
    EnumDescriptorProto,
    FieldDescriptorProto,
    FileDescriptorProto,
    ServiceDescriptorProto,
)
from betterproto.lib.google.protobuf.compiler import (
    CodeGeneratorRequest,
    CodeGeneratorResponse,
    CodeGeneratorResponseFile,
)
import itertools
import pathlib
import sys
from typing import Iterator, List, Set, Tuple, TYPE_CHECKING, Union
from .compiler import outputfile_compiler
from .models import (
    EnumDefinitionCompiler,
    FieldCompiler,
    MapEntryCompiler,
    MessageCompiler,
    OneOfFieldCompiler,
    OutputTemplate,
    PluginRequestCompiler,
    ServiceCompiler,
    ServiceMethodCompiler,
    is_map,
    is_oneof,
)

if TYPE_CHECKING:
    from google.protobuf.descriptor import Descriptor


def traverse(
    proto_file: FieldDescriptorProto,
) -> "itertools.chain[Tuple[Union[str, EnumDescriptorProto], List[int]]]":
    # Todo: Keep information about nested hierarchy
    def _traverse(
        path: List[int], items: List["EnumDescriptorProto"], prefix=""
    ) -> Iterator[Tuple[Union[str, EnumDescriptorProto], List[int]]]:
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
    request: CodeGeneratorRequest, response: CodeGeneratorResponse
) -> None:
    plugin_options = request.parameter.split(",") if request.parameter else []

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
                read_protobuf_type(
                    source_file=proto_input_file,
                    item=item,
                    path=path,
                    output_package=output_package,
                )

    # Read Services
    for output_package_name, output_package in request_data.output_packages.items():
        for proto_input_file in output_package.input_files:
            for index, service in enumerate(proto_input_file.service):
                read_protobuf_service(service, index, output_package)

    # Generate output files
    output_paths: Set[pathlib.Path] = set()
    for output_package_name, output_package in request_data.output_packages.items():

        # Add files to the response object
        output_path = pathlib.Path(*output_package_name.split("."), "__init__.py")
        output_paths.add(output_path)

        response.file.append(
            CodeGeneratorResponseFile(
                name=str(output_path),
                # Render and then format the output file
                content=outputfile_compiler(output_file=output_package),
            )
        )

    # Make each output directory a package with __init__ file
    init_files = {
        directory.joinpath("__init__.py")
        for path in output_paths
        for directory in path.parents
    } - output_paths

    for init_file in init_files:
        response.file.append(CodeGeneratorResponseFile(name=str(init_file)))

    for output_package_name in sorted(output_paths.union(init_files)):
        print(f"Writing {output_package_name}", file=sys.stderr)


def read_protobuf_type(
    item: DescriptorProto,
    path: List[int],
    source_file: "FileDescriptorProto",
    output_package: OutputTemplate,
) -> None:
    if isinstance(item, DescriptorProto):
        if item.options.map_entry:
            # Skip generated map entry messages since we just use dicts
            return
        # Process Message
        message_data = MessageCompiler(
            source_file=source_file, parent=output_package, proto_obj=item, path=path
        )
        for index, field in enumerate(item.field):
            if is_map(field, item):
                MapEntryCompiler(
                    source_file=source_file,
                    parent=message_data,
                    proto_obj=field,
                    path=path + [2, index],
                )
            elif is_oneof(field):
                OneOfFieldCompiler(
                    source_file=source_file,
                    parent=message_data,
                    proto_obj=field,
                    path=path + [2, index],
                )
            else:
                FieldCompiler(
                    source_file=source_file,
                    parent=message_data,
                    proto_obj=field,
                    path=path + [2, index],
                )
    elif isinstance(item, EnumDescriptorProto):
        # Enum
        EnumDefinitionCompiler(
            source_file=source_file, parent=output_package, proto_obj=item, path=path
        )


def read_protobuf_service(
    service: ServiceDescriptorProto, index: int, output_package: OutputTemplate
) -> None:
    service_data = ServiceCompiler(
        parent=output_package, proto_obj=service, path=[6, index]
    )
    for j, method in enumerate(service.method):
        ServiceMethodCompiler(
            parent=service_data, proto_obj=method, path=[6, index, 2, j]
        )
