import pytest

from betterproto.lib.google.protobuf import (
    DescriptorProto,
    EnumDescriptorProto,
    EnumValueDescriptorProto,
    FieldDescriptorProto,
    FieldDescriptorProtoType,
    FileDescriptorProto,
    MethodDescriptorProto,
    ServiceDescriptorProto,
    SourceCodeInfo,
    SourceCodeInfoLocation,
)
from betterproto.lib.google.protobuf.compiler import CodeGeneratorRequest
from betterproto.plugin.models import PluginRequestCompiler, get_comment
from betterproto.plugin.parser import generate_code


@pytest.mark.parametrize("indent", [0, 4, 8])
def test_indexed_comments_preserve_formatting(indent):
    locations = [
        SourceCodeInfoLocation(
            path=[4, i],
            leading_detached_comments=detached,
            leading_comments=leading,
            trailing_comments=trailing,
        )
        for i, (detached, leading, trailing) in enumerate(
            [
                ([], "", ""),
                ([], " A short comment.", ""),
                ([], "\n\n Leading\n\n\n lines.\n", ""),
                (
                    [" Detached one.\n", " Detached two.\n"],
                    " Leading.\n",
                    " Trailing.\n",
                ),
                ([], " A long comment " * 10, ""),
                ([], "\tUnicode: \u03bb\u4e2d\u6587", ""),
            ]
        )
    ]
    # A repeated path must keep the first location, even if it has no comment.
    locations.append(SourceCodeInfoLocation(path=[4, 0], leading_comments=" Later."))
    source = FileDescriptorProto(source_code_info=SourceCodeInfo(location=locations))
    compiler = PluginRequestCompiler(CodeGeneratorRequest(proto_file=[source]))

    for path in [[4, i] for i in range(6)] + [[4, 99], [], [4]]:
        assert compiler.get_comment(source, path, indent) == get_comment(
            source, path, indent
        )


def test_comment_index_is_scoped_to_source_file_and_request():
    first = FileDescriptorProto(
        name="first.proto",
        source_code_info=SourceCodeInfo(
            location=[SourceCodeInfoLocation(path=[4, 0], leading_comments=" First.")]
        ),
    )
    second = FileDescriptorProto(
        name="second.proto",
        source_code_info=SourceCodeInfo(
            location=[SourceCodeInfoLocation(path=[4, 0], leading_comments=" Second.")]
        ),
    )
    request = CodeGeneratorRequest(proto_file=[first, second])
    compiler = PluginRequestCompiler(request)
    assert compiler.get_comment(first, [4, 0]) == '    """First."""'
    assert compiler.get_comment(second, [4, 0]) == '    """Second."""'

    first.source_code_info.location[0].path = [4, 1]
    next_compiler = PluginRequestCompiler(request)
    assert next_compiler.get_comment(first, [4, 0]) == ""
    assert next_compiler.get_comment(first, [4, 1]) == '    """First."""'


def test_generated_comments_do_not_repeatedly_scan_locations(monkeypatch):
    field_count = 100
    sources = []
    for file_index in range(2):
        locations = [
            SourceCodeInfoLocation(
                path=[4, 0], leading_comments=f" Message {file_index}."
            )
        ]
        fields = []
        for i in range(field_count):
            fields.append(
                FieldDescriptorProto(
                    name=f"field_{i}",
                    number=i + 1,
                    type=FieldDescriptorProtoType.TYPE_STRING,
                )
            )
            locations.append(
                SourceCodeInfoLocation(
                    path=[4, 0, 2, i], leading_comments=f" Field {file_index}/{i}."
                )
            )
        locations += [
            SourceCodeInfoLocation(
                path=[5, 0], leading_comments=f" Enum {file_index}."
            ),
            SourceCodeInfoLocation(
                path=[5, 0, 2, 0], leading_comments=f" Entry {file_index}."
            ),
            SourceCodeInfoLocation(
                path=[6, 0], leading_comments=f" Service {file_index}."
            ),
            SourceCodeInfoLocation(
                path=[6, 0, 2, 0], leading_comments=f" Method {file_index}."
            ),
        ]
        sources.append(
            FileDescriptorProto(
                name=f"file_{file_index}.proto",
                package="comments",
                message_type=[
                    DescriptorProto(name=f"Message{file_index}", field=fields)
                ],
                enum_type=[
                    EnumDescriptorProto(
                        name=f"Enum{file_index}",
                        value=[EnumValueDescriptorProto(name="ZERO", number=0)],
                    )
                ],
                service=[
                    ServiceDescriptorProto(
                        name=f"Service{file_index}",
                        method=[
                            MethodDescriptorProto(
                                name="Call",
                                input_type=f".comments.Message{file_index}",
                                output_type=f".comments.Message{file_index}",
                            )
                        ],
                    )
                ],
                source_code_info=SourceCodeInfo(location=locations),
            )
        )

    path_reads = 0
    original_getattribute = SourceCodeInfoLocation.__getattribute__

    def count_path_reads(self, name):
        nonlocal path_reads
        if name == "path":
            path_reads += 1
        return original_getattribute(self, name)

    monkeypatch.setattr(SourceCodeInfoLocation, "__getattribute__", count_path_reads)
    response = generate_code(CodeGeneratorRequest(proto_file=sources))
    content = "\n".join(file.content for file in response.file)
    for file_index in range(2):
        for kind in ("Message", "Enum", "Entry", "Service", "Method"):
            assert f"{kind} {file_index}." in content
        for i in range(field_count):
            assert f"Field {file_index}/{i}." in content

    # Each source location may be indexed and checked a few times, but the
    # number of reads must grow linearly with the number of declarations.
    assert path_reads < 10 * sum(
        len(source.source_code_info.location) for source in sources
    )
