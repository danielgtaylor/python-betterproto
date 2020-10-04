"""Plugin model dataclasses.

These classes are meant to be an intermediate representation
of protbuf objects. They are used to organize the data collected during parsing.

The general intention is to create a doubly-linked tree-like structure
with the following types of references:
- Downwards references: from message -> fields, from output package -> messages
or from service -> service methods
- Upwards references: from field -> message, message -> package.
- Input/ouput message references: from a service method to it's corresponding
input/output messages, which may even be in another package.

There are convenience methods to allow climbing up and down this tree, for
example to retrieve the list of all messages that are in the same package as
the current message.

Most of these classes take as inputs:
- proto_obj: A reference to it's corresponding protobuf object as
presented by the protoc plugin.
- parent: a reference to the parent object in the tree.

With this information, the class is able to expose attributes,
such as a pythonized name, that will be calculated from proto_obj.

The instantiation should also attach a reference to the new object
into the corresponding place within it's parent object. For example,
instantiating field `A` with parent message `B` should add a
reference to `A` to `B`'s `fields` attirbute.
"""

import betterproto
from betterproto.casing import sanitize_name
from betterproto.compile.importing import (
    get_type_reference,
    parse_source_type_name,
)
from betterproto.compile.naming import (
    pythonize_class_name,
    pythonize_field_name,
    pythonize_method_name,
)
from betterproto.lib.google.protobuf import (
    DescriptorProto,
    EnumDescriptorProto,
    FileDescriptorProto,
    MethodDescriptorProto,
    FieldDescriptorProto,
    FieldDescriptorProtoType,
    FieldDescriptorProtoLabel,
)
from betterproto.lib.google.protobuf.compiler import CodeGeneratorRequest
from dataclasses import dataclass
from dataclasses import field
import re
import textwrap
from typing import (
    Iterator,
    Union,
    Type,
    List,
    Dict,
    Set,
    Text,
)

# Create a unique placeholder to deal with
# https://stackoverflow.com/questions/51575931/class-inheritance-in-python-3-7-dataclasses
PLACEHOLDER = object()

# Organize proto types into categories
PROTO_FLOAT_TYPES = (
    FieldDescriptorProtoType.TYPE_DOUBLE,  # 1
    FieldDescriptorProtoType.TYPE_FLOAT,  # 2
)
PROTO_INT_TYPES = (
    FieldDescriptorProtoType.TYPE_INT64,  # 3
    FieldDescriptorProtoType.TYPE_UINT64,  # 4
    FieldDescriptorProtoType.TYPE_INT32,  # 5
    FieldDescriptorProtoType.TYPE_FIXED64,  # 6
    FieldDescriptorProtoType.TYPE_FIXED32,  # 7
    FieldDescriptorProtoType.TYPE_UINT32,  # 13
    FieldDescriptorProtoType.TYPE_SFIXED32,  # 15
    FieldDescriptorProtoType.TYPE_SFIXED64,  # 16
    FieldDescriptorProtoType.TYPE_SINT32,  # 17
    FieldDescriptorProtoType.TYPE_SINT64,  # 18
)
PROTO_BOOL_TYPES = (FieldDescriptorProtoType.TYPE_BOOL,)  # 8
PROTO_STR_TYPES = (FieldDescriptorProtoType.TYPE_STRING,)  # 9
PROTO_BYTES_TYPES = (FieldDescriptorProtoType.TYPE_BYTES,)  # 12
PROTO_MESSAGE_TYPES = (
    FieldDescriptorProtoType.TYPE_MESSAGE,  # 11
    FieldDescriptorProtoType.TYPE_ENUM,  # 14
)
PROTO_MAP_TYPES = (FieldDescriptorProtoType.TYPE_MESSAGE,)  # 11
PROTO_PACKED_TYPES = (
    FieldDescriptorProtoType.TYPE_DOUBLE,  # 1
    FieldDescriptorProtoType.TYPE_FLOAT,  # 2
    FieldDescriptorProtoType.TYPE_INT64,  # 3
    FieldDescriptorProtoType.TYPE_UINT64,  # 4
    FieldDescriptorProtoType.TYPE_INT32,  # 5
    FieldDescriptorProtoType.TYPE_FIXED64,  # 6
    FieldDescriptorProtoType.TYPE_FIXED32,  # 7
    FieldDescriptorProtoType.TYPE_BOOL,  # 8
    FieldDescriptorProtoType.TYPE_UINT32,  # 13
    FieldDescriptorProtoType.TYPE_SFIXED32,  # 15
    FieldDescriptorProtoType.TYPE_SFIXED64,  # 16
    FieldDescriptorProtoType.TYPE_SINT32,  # 17
    FieldDescriptorProtoType.TYPE_SINT64,  # 18
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


class ProtoContentBase:
    """Methods common to MessageCompiler, ServiceCompiler and ServiceMethodCompiler."""

    path: List[int]
    comment_indent: int = 4
    parent: Union["Messsage", "OutputTemplate"]

    def __post_init__(self):
        """Checks that no fake default fields were left as placeholders."""
        for field_name, field_val in self.__dataclass_fields__.items():
            if field_val is PLACEHOLDER:
                raise ValueError(f"`{field_name}` is a required field.")

    @property
    def output_file(self) -> "OutputTemplate":
        current = self
        while not isinstance(current, OutputTemplate):
            current = current.parent
        return current

    @property
    def proto_file(self) -> FieldDescriptorProto:
        current = self
        while not isinstance(current, OutputTemplate):
            current = current.parent
        return current.package_proto_obj

    @property
    def request(self) -> "PluginRequestCompiler":
        current = self
        while not isinstance(current, OutputTemplate):
            current = current.parent
        return current.parent_request

    @property
    def comment(self) -> str:
        """Crawl the proto source code and retrieve comments
        for this object.
        """
        return get_comment(
            proto_file=self.proto_file, path=self.path, indent=self.comment_indent
        )


@dataclass
class PluginRequestCompiler:

    plugin_request_obj: CodeGeneratorRequest
    output_packages: Dict[str, "OutputTemplate"] = field(default_factory=dict)

    @property
    def all_messages(self) -> List["MessageCompiler"]:
        """All of the messages in this request.

        Returns
        -------
        List[MessageCompiler]
            List of all of the messages in this request.
        """
        return [
            msg for output in self.output_packages.values() for msg in output.messages
        ]


@dataclass
class OutputTemplate:
    """Representation of an output .py file.

    Each output file corresponds to a .proto input file,
    but may need references to other .proto files to be
    built.
    """

    parent_request: PluginRequestCompiler
    package_proto_obj: FileDescriptorProto
    input_files: List[str] = field(default_factory=list)
    imports: Set[str] = field(default_factory=set)
    datetime_imports: Set[str] = field(default_factory=set)
    typing_imports: Set[str] = field(default_factory=set)
    messages: List["MessageCompiler"] = field(default_factory=list)
    enums: List["EnumDefinitionCompiler"] = field(default_factory=list)
    services: List["ServiceCompiler"] = field(default_factory=list)

    @property
    def package(self) -> str:
        """Name of input package.

        Returns
        -------
        str
            Name of input package.
        """
        return self.package_proto_obj.package

    @property
    def input_filenames(self) -> List[str]:
        """Names of the input files used to build this output.

        Returns
        -------
        List[str]
            Names of the input files used to build this output.
        """
        return [f.name for f in self.input_files]

    @property
    def python_module_imports(self) -> Set[str]:
        imports = set()
        if any(x for x in self.messages if any(x.deprecated_fields)):
            imports.add("warnings")
        return imports


@dataclass
class MessageCompiler(ProtoContentBase):
    """Representation of a protobuf message."""

    parent: Union["MessageCompiler", OutputTemplate] = PLACEHOLDER
    proto_obj: DescriptorProto = PLACEHOLDER
    path: List[int] = PLACEHOLDER
    fields: List[Union["FieldCompiler", "MessageCompiler"]] = field(
        default_factory=list
    )
    deprecated: bool = field(default=False, init=False)

    def __post_init__(self):
        # Add message to output file
        if isinstance(self.parent, OutputTemplate):
            if isinstance(self, EnumDefinitionCompiler):
                self.output_file.enums.append(self)
            else:
                self.output_file.messages.append(self)
        self.deprecated = self.proto_obj.options.deprecated
        super().__post_init__()

    @property
    def proto_name(self) -> str:
        return self.proto_obj.name

    @property
    def py_name(self) -> str:
        return pythonize_class_name(self.proto_name)

    @property
    def annotation(self) -> str:
        if self.repeated:
            return f"List[{self.py_name}]"
        return self.py_name

    @property
    def deprecated_fields(self) -> Iterator[str]:
        for f in self.fields:
            if f.deprecated:
                yield f.py_name


def is_map(
    proto_field_obj: FieldDescriptorProto, parent_message: DescriptorProto
) -> bool:
    """True if proto_field_obj is a map, otherwise False."""
    if proto_field_obj.type == FieldDescriptorProtoType.TYPE_MESSAGE:
        # This might be a map...
        message_type = proto_field_obj.type_name.split(".").pop().lower()
        map_entry = f"{proto_field_obj.name.replace('_', '').lower()}entry"
        if message_type == map_entry:
            for nested in parent_message.nested_type:  # parent message
                if nested.name.replace("_", "").lower() == map_entry:
                    if nested.options.map_entry:
                        return True
    return False


def is_oneof(proto_field_obj: FieldDescriptorProto) -> bool:
    """True if proto_field_obj is a OneOf, otherwise False."""

    # FIXME
    # if proto_field_obj.HasField("oneof_index"):
    if proto_field_obj.oneof_index:
        return True
    return False

import ptvsd
ptvsd.enable_attach()
ptvsd.wait_for_attach()  # blocks execution until debugger is attached

@dataclass
class FieldCompiler(MessageCompiler):
    parent: MessageCompiler = PLACEHOLDER
    proto_obj: FieldDescriptorProto = PLACEHOLDER

    def __post_init__(self):
        # Add field to message
        self.parent.fields.append(self)
        # Check for new imports
        annotation = self.annotation
        if self.proto_obj.name == "email":
            import sys
            print(self.proto_obj.options, file=sys.stderr)
        if "Optional[" in annotation:
            self.output_file.typing_imports.add("Optional")
        if "List[" in annotation:
            self.output_file.typing_imports.add("List")
        if "Dict[" in annotation:
            self.output_file.typing_imports.add("Dict")
        if "timedelta" in annotation:
            self.output_file.datetime_imports.add("timedelta")
        if "datetime" in annotation:
            self.output_file.datetime_imports.add("datetime")
        super().__post_init__()  # call FieldCompiler-> MessageCompiler __post_init__

    def get_field_string(self, indent: int = 4) -> str:
        """Construct string representation of this field as a field."""
        name = f"{self.py_name}"
        annotations = f": {self.annotation}"
        field_args = ", ".join(
            ([""] + self.betterproto_field_args) if self.betterproto_field_args else []
        )
        betterproto_field_type = (
            f"betterproto.{self.field_type}_field({self.proto_obj.number}"
            + field_args
            + ")"
        )
        return name + annotations + " = " + betterproto_field_type

    @property
    def betterproto_field_args(self) -> List[str]:
        args = []
        if self.field_wraps:
            args.append(f"wraps={self.field_wraps}")
        return args

    @property
    def field_wraps(self) -> Union[str, None]:
        """Returns betterproto wrapped field type or None."""
        match_wrapper = re.match(
            r"\.google\.protobuf\.(.+)Value", self.proto_obj.type_name
        )
        if match_wrapper:
            wrapped_type = "TYPE_" + match_wrapper.group(1).upper()
            if hasattr(betterproto, wrapped_type):
                return f"betterproto.{wrapped_type}"
        return None

    @property
    def repeated(self) -> bool:
        if (
            self.proto_obj.label == FieldDescriptorProtoLabel.LABEL_REPEATED
            and not is_map(self.proto_obj, self.parent)
        ):
            return True
        return False

    @property
    def mutable(self) -> bool:
        """True if the field is a mutable type, otherwise False."""
        annotation = self.annotation
        return annotation.startswith("List[") or annotation.startswith("Dict[")

    @property
    def field_type(self) -> str:
        """String representation of proto field type."""
        return (
            FieldDescriptorProtoType(self.proto_obj.type)
            .name.lower()
            .replace("type_", "")
        )

    @property
    def default_value_string(self) -> Union[Text, None, float, int]:
        """Python representation of the default proto value."""
        if self.repeated:
            return "[]"
        if self.py_type == "int":
            return "0"
        if self.py_type == "float":
            return "0.0"
        elif self.py_type == "bool":
            return "False"
        elif self.py_type == "str":
            return '""'
        elif self.py_type == "bytes":
            return 'b""'
        else:
            # Message type
            return "None"

    @property
    def packed(self) -> bool:
        """True if the wire representation is a packed format."""
        if self.repeated and self.proto_obj.type in PROTO_PACKED_TYPES:
            return True
        return False

    @property
    def py_name(self) -> str:
        """Pythonized name."""
        return pythonize_field_name(self.proto_name)

    @property
    def proto_name(self) -> str:
        """Original protobuf name."""
        return self.proto_obj.name

    @property
    def py_type(self) -> str:
        """String representation of Python type."""
        if self.proto_obj.type in PROTO_FLOAT_TYPES:
            return "float"
        elif self.proto_obj.type in PROTO_INT_TYPES:
            return "int"
        elif self.proto_obj.type in PROTO_BOOL_TYPES:
            return "bool"
        elif self.proto_obj.type in PROTO_STR_TYPES:
            return "str"
        elif self.proto_obj.type in PROTO_BYTES_TYPES:
            return "bytes"
        elif self.proto_obj.type in PROTO_MESSAGE_TYPES:
            # Type referencing another defined Message or a named enum
            return get_type_reference(
                package=self.output_file.package,
                imports=self.output_file.imports,
                source_type=self.proto_obj.type_name,
            )
        else:
            raise NotImplementedError(f"Unknown type {field.type}")

    @property
    def annotation(self) -> str:
        if self.repeated:
            return f"List[{self.py_type}]"
        return self.py_type


@dataclass
class OneOfFieldCompiler(FieldCompiler):
    @property
    def betterproto_field_args(self) -> List[str]:
        args = super().betterproto_field_args
        group = self.parent.proto_obj.oneof_decl[self.proto_obj.oneof_index].name
        args.append(f'group="{group}"')
        return args


@dataclass
class MapEntryCompiler(FieldCompiler):
    py_k_type: Type = PLACEHOLDER
    py_v_type: Type = PLACEHOLDER
    proto_k_type: str = PLACEHOLDER
    proto_v_type: str = PLACEHOLDER

    def __post_init__(self):
        """Explore nested types and set k_type and v_type if unset."""
        map_entry = f"{self.proto_obj.name.replace('_', '').lower()}entry"
        for nested in self.parent.proto_obj.nested_type:
            if nested.name.replace("_", "").lower() == map_entry:
                if nested.options.map_entry:
                    # Get Python types
                    self.py_k_type = FieldCompiler(
                        parent=self, proto_obj=nested.field[0]  # key
                    ).py_type
                    self.py_v_type = FieldCompiler(
                        parent=self, proto_obj=nested.field[1]  # value
                    ).py_type
                    # Get proto types
                    self.proto_k_type = self.proto_obj.Type.Name(nested.field[0].type)
                    self.proto_v_type = self.proto_obj.Type.Name(nested.field[1].type)
        super().__post_init__()  # call FieldCompiler-> MessageCompiler __post_init__

    @property
    def betterproto_field_args(self) -> List[str]:
        return [f"betterproto.{self.proto_k_type}", f"betterproto.{self.proto_v_type}"]

    @property
    def field_type(self) -> str:
        return "map"

    @property
    def annotation(self):
        return f"Dict[{self.py_k_type}, {self.py_v_type}]"

    @property
    def repeated(self):
        return False  # maps cannot be repeated


@dataclass
class EnumDefinitionCompiler(MessageCompiler):
    """Representation of a proto Enum definition."""

    proto_obj: EnumDescriptorProto = PLACEHOLDER
    entries: List["EnumDefinitionCompiler.EnumEntry"] = PLACEHOLDER

    @dataclass(unsafe_hash=True)
    class EnumEntry:
        """Representation of an Enum entry."""

        name: str
        value: int
        comment: str

    def __post_init__(self):
        # import sys

        # sys.stderr.write(f"self.proto_obj: {self.proto_obj}")
        # Get entries/allowed values for this Enum
        self.entries = [
            self.EnumEntry(
                # FIXME: work out why the we're getting the wrong Message type (and no enum names)
                #        maybe something wrong with the betterproto generated compiler methods?
                # name=sanitize_name(entry_proto_value.name),
                # value=entry_proto_value.number,
                name=sanitize_name(entry_proto_value),
                value=entry_proto_value,
                comment=get_comment(
                    proto_file=self.proto_file, path=self.path + [2, entry_number]
                ),
            )
            for entry_number, entry_proto_value in enumerate(self.proto_obj.value)
        ]
        super().__post_init__()  # call MessageCompiler __post_init__

    @property
    def default_value_string(self) -> int:
        """Python representation of the default value for Enums.

        As per the spec, this is the first value of the Enum.
        """
        return str(self.entries[0].value)  # ideally, should ALWAYS be int(0)!


@dataclass
class ServiceCompiler(ProtoContentBase):
    parent: OutputTemplate = PLACEHOLDER
    proto_obj: DescriptorProto = PLACEHOLDER
    path: List[int] = PLACEHOLDER
    methods: List["ServiceMethodCompiler"] = field(default_factory=list)

    def __post_init__(self) -> None:
        # Add service to output file
        self.output_file.services.append(self)
        super().__post_init__()  # check for unset fields

    @property
    def proto_name(self):
        return self.proto_obj.name

    @property
    def py_name(self):
        return pythonize_class_name(self.proto_name)


@dataclass
class ServiceMethodCompiler(ProtoContentBase):

    parent: ServiceCompiler
    proto_obj: MethodDescriptorProto
    path: List[int] = PLACEHOLDER
    comment_indent: int = 8

    def __post_init__(self) -> None:
        # Add method to service
        self.parent.methods.append(self)

        # Check for Optional import
        if self.py_input_message:
            for f in self.py_input_message.fields:
                if f.default_value_string == "None":
                    self.output_file.typing_imports.add("Optional")
        if "Optional" in self.py_output_message_type:
            self.output_file.typing_imports.add("Optional")
        self.mutable_default_args  # ensure this is called before rendering

        # Check for Async imports
        if self.client_streaming:
            self.output_file.typing_imports.add("AsyncIterable")
            self.output_file.typing_imports.add("Iterable")
            self.output_file.typing_imports.add("Union")
        if self.server_streaming:
            self.output_file.typing_imports.add("AsyncIterator")

        super().__post_init__()  # check for unset fields

    @property
    def mutable_default_args(self) -> Dict[str, str]:
        """Handle mutable default arguments.

        Returns a list of tuples containing the name and default value
        for arguments to this message who's default value is mutable.
        The defaults are swapped out for None and replaced back inside
        the method's body.
        Reference:
        https://docs.python-guide.org/writing/gotchas/#mutable-default-arguments

        Returns
        -------
        Dict[str, str]
            Name and actual default value (as a string)
            for each argument with mutable default values.
        """
        mutable_default_args = dict()

        if self.py_input_message:
            for f in self.py_input_message.fields:
                if (
                    not self.client_streaming
                    and f.default_value_string != "None"
                    and f.mutable
                ):
                    mutable_default_args[f.py_name] = f.default_value_string
                    self.output_file.typing_imports.add("Optional")

        return mutable_default_args

    @property
    def py_name(self) -> str:
        """Pythonized method name."""
        return pythonize_method_name(self.proto_obj.name)

    @property
    def proto_name(self) -> str:
        """Original protobuf name."""
        return self.proto_obj.name

    @property
    def route(self) -> str:
        return (
            f"/{self.output_file.package}."
            f"{self.parent.proto_name}/{self.proto_name}"
        )

    @property
    def py_input_message(self) -> Union[None, MessageCompiler]:
        """Find the input message object.

        Returns
        -------
        Union[None, MessageCompiler]
            Method instance representing the input message.
            If not input message could be found or there are no
            input messages, None is returned.
        """
        package, name = parse_source_type_name(self.proto_obj.input_type)

        # Nested types are currently flattened without dots.
        # Todo: keep a fully quantified name in types, that is
        # comparable with method.input_type
        for msg in self.request.all_messages:
            if (
                msg.py_name == name.replace(".", "")
                and msg.output_file.package == package
            ):
                return msg
        return None

    @property
    def py_input_message_type(self) -> str:
        """String representation of the Python type correspoding to the
        input message.

        Returns
        -------
        str
            String representation of the Python type correspoding to the
        input message.
        """
        return get_type_reference(
            package=self.output_file.package,
            imports=self.output_file.imports,
            source_type=self.proto_obj.input_type,
        ).strip('"')

    @property
    def py_output_message_type(self) -> str:
        """String representation of the Python type correspoding to the
        output message.

        Returns
        -------
        str
            String representation of the Python type correspoding to the
        output message.
        """
        return get_type_reference(
            package=self.output_file.package,
            imports=self.output_file.imports,
            source_type=self.proto_obj.output_type,
            unwrap=False,
        ).strip('"')

    @property
    def client_streaming(self) -> bool:
        return self.proto_obj.client_streaming

    @property
    def server_streaming(self) -> bool:
        return self.proto_obj.server_streaming
