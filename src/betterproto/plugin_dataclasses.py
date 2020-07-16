#!/usr/bin/env python
from __future__ import annotations

import re
from dataclasses import dataclass
from dataclasses import field
from typing import (
    Union,
    Type,
    List,
    Set,
    Text,
)
import textwrap

import betterproto
from betterproto.compile.importing import (
    get_type_reference,
    parse_source_type_name,
)
from betterproto.compile.naming import (
    pythonize_class_name,
    pythonize_field_name,
    pythonize_method_name,
)

try:
    # betterproto[compiler] specific dependencies
    from google.protobuf.descriptor_pb2 import (
        DescriptorProto,
        EnumDescriptorProto,
        FieldDescriptorProto,
        FileDescriptorProto,
        MethodDescriptorProto,
    )
except ImportError as err:
    missing_import = re.match(
        r".*(cannot import name .*$)", err.args[0]
    ).group(1)
    print(
        "\033[31m"
        f"Unable to import `{missing_import}` from betterproto plugin! "
        "Please ensure that you've installed betterproto as "
        '`pip install "betterproto[compiler]"` so that compiler dependencies '
        "are included."
        "\033[0m"
    )
    raise SystemExit(1)

# Create a unique placeholder to deal with
# https://stackoverflow.com/questions/51575931/class-inheritance-in-python-3-7-dataclasses
PLACEHOLDER = object()

# Organize proto types into categories
PROTO_FLOAT_TYPES = (
    FieldDescriptorProto.TYPE_DOUBLE,  # 1
    FieldDescriptorProto.TYPE_FLOAT,  # 2
)
PROTO_INT_TYPES = (
    FieldDescriptorProto.TYPE_INT64,  # 3
    FieldDescriptorProto.TYPE_UINT64,  # 4
    FieldDescriptorProto.TYPE_INT32,  # 5
    FieldDescriptorProto.TYPE_FIXED64,  # 6
    FieldDescriptorProto.TYPE_FIXED32,  # 7
    FieldDescriptorProto.TYPE_UINT32,  # 13
    FieldDescriptorProto.TYPE_SFIXED32,  # 15
    FieldDescriptorProto.TYPE_SFIXED64,  # 16
    FieldDescriptorProto.TYPE_SINT32,  # 17
    FieldDescriptorProto.TYPE_SINT64,  # 18
)
PROTO_BOOL_TYPES = (FieldDescriptorProto.TYPE_BOOL,)  # 8
PROTO_STR_TYPES = (FieldDescriptorProto.TYPE_STRING,)  # 9
PROTO_BYTES_TYPES = (FieldDescriptorProto.TYPE_BYTES,)  # 12
PROTO_MESSAGE_TYPES = (
    FieldDescriptorProto.TYPE_MESSAGE,  # 11
    FieldDescriptorProto.TYPE_ENUM,  # 14
)
PROTO_MAP_TYPES = (FieldDescriptorProto.TYPE_MESSAGE,)  # 11
PROTO_PACKED_TYPES = (
    FieldDescriptorProto.TYPE_DOUBLE,  # 1
    FieldDescriptorProto.TYPE_FLOAT,  # 2
    FieldDescriptorProto.TYPE_INT64,  # 3
    FieldDescriptorProto.TYPE_UINT64,  # 4
    FieldDescriptorProto.TYPE_INT32,  # 5
    FieldDescriptorProto.TYPE_FIXED64,  # 6
    FieldDescriptorProto.TYPE_FIXED32,  # 7
    FieldDescriptorProto.TYPE_BOOL,  # 8
    FieldDescriptorProto.TYPE_UINT32,  # 13
    FieldDescriptorProto.TYPE_SFIXED32,  # 15
    FieldDescriptorProto.TYPE_SFIXED64,  # 16
    FieldDescriptorProto.TYPE_SINT32,  # 17
    FieldDescriptorProto.TYPE_SINT64,  # 18
)


def get_comment(proto_file, path: List[int], indent: int = 4) -> str:
    pad = " " * indent
    for sci in proto_file.source_code_info.location:
        # print(list(sci.path), path, file=sys.stderr)
        if list(sci.path) == path and sci.leading_comments:
            lines = textwrap.wrap(
                sci.leading_comments.strip().replace("\n", ""),
                width=79 - indent,
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
    """Methods common to Message, Service and ServiceMethod."""

    path: List[int]
    comment_indent: int = 4

    def __post_init__(self):
        """Checks that no fake default fields were left as placeholders."""
        for field_name, field_val in self.__dataclass_fields__.items():
            if field_val is PLACEHOLDER:
                raise ValueError(
                    f"`{field_name}` is a required field."
                )

    @property
    def output_file(self) -> OutputTemplate:
        current = self.parent
        while not isinstance(current, OutputTemplate):
            current = current.parent
        return current

    @property
    def proto_file(self) -> FieldDescriptorProto:
        current = self
        while not isinstance(current, ProtoInputFile):
            current = current.parent
        return current.proto_obj

    @property
    def comment(self) -> str:
        """Crawl the proto source code and retrieve comments
        for this object.
        """
        return get_comment(
            proto_file=self.proto_file,
            path=self.path,
            indent=self.comment_indent,
        )


@dataclass
class OutputTemplate:
    """Representation of an output .py file.
    """

    input_package: str
    input_files: List[ProtoInputFile] = field(default_factory=list)
    imports: Set[str] = field(default_factory=set)
    datetime_imports: Set[str] = field(default_factory=set)
    typing_imports: Set[str] = field(default_factory=set)
    messages: List[Message] = field(default_factory=list)
    enums: List[EnumDefinition] = field(default_factory=list)
    services: List[Service] = field(default_factory=list)

    @property
    def input_filenames(self) -> List[str]:
        return [f.name for f in self.input_files]


@dataclass
class ProtoInputFile:
    """Representation of an input .proto file.
    """

    parent: OutputTemplate
    proto_obj: FileDescriptorProto

    @property
    def name(self) -> str:
        return self.proto_obj.name

    def __post_init__(self):
        # Add proto file to output file
        self.parent.input_files.append(self)


@dataclass
class Message(ProtoContentBase):
    """Representation of a protobuf message.
    """

    parent: Union[ProtoInputFile, Message] = PLACEHOLDER
    proto_obj: DescriptorProto = PLACEHOLDER
    path: List[int] = PLACEHOLDER
    fields: List[Union[Field, Message]] = field(default_factory=list)

    def __post_init__(self):
        # Add message to output file
        if isinstance(self.parent, ProtoInputFile):
            if isinstance(self, EnumDefinition):
                self.output_file.enums.append(self)
            else:
                self.output_file.messages.append(self)
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


def is_map(
    proto_field_obj: FieldDescriptorProto, parent_message: DescriptorProto
) -> bool:
    """True if proto_field_obj is a map, otherwise False.
    """
    if proto_field_obj.type == FieldDescriptorProto.TYPE_MESSAGE:
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
    """True if proto_field_obj is a OneOf, otherwise False.
    """
    if proto_field_obj.HasField("oneof_index"):
        return True
    return False


@dataclass
class Field(Message):
    parent: Message = PLACEHOLDER
    proto_obj: FieldDescriptorProto = PLACEHOLDER

    def __post_init__(self):
        # Add field to message
        self.parent.fields.append(self)
        # Check for new imports
        annotation = self.annotation
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
        super().__post_init__()  # call Field -> Message __post_init__

    def get_field_string(self, indent: int = 4) -> str:
        """Construct string representation of this field as a field."""
        name = f"{self.py_name}"
        annotations = f": {self.annotation}"
        betterproto_field_type = (
            f"betterproto.{self.field_type}_field({self.proto_obj.number}"
            + f"{self.betterproto_field_args}"
            + ")"
        )
        return name + annotations + " = " + betterproto_field_type

    @property
    def betterproto_field_args(self):
        args = ""
        if self.field_wraps:
            args = args + f", wraps={self.field_wraps}"
        return args

    @property
    def field_wraps(self) -> Union[str, None]:
        """Returns betterproto wrapped field type or None.
        """
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
            self.proto_obj.label == FieldDescriptorProto.LABEL_REPEATED
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
            self.proto_obj.Type.Name(self.proto_obj.type)
            .lower()
            .replace("type_", "")
        )

    @property
    def default_value_string(self) -> Union[Text, None, float, int]:
        """Python representation of the default proto value.
        """
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
                package=self.output_file.input_package,
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
class OneOfField(Field):
    @property
    def betterproto_field_args(self):
        args = super().betterproto_field_args
        group = self.parent.proto_obj.oneof_decl[
            self.proto_obj.oneof_index
        ].name
        args = (
            args
            + f', group="{group}"'
        )
        return args


@dataclass
class MapField(Field):
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
                    self.py_k_type = Field(
                        parent=self, proto_obj=nested.field[0],  # key
                    ).py_type
                    self.py_v_type = Field(
                        parent=self, proto_obj=nested.field[1],  # key
                    ).py_type
                    # Get proto types
                    self.proto_k_type = self.proto_obj.Type.Name(
                        nested.field[0].type
                    )
                    self.proto_v_type = self.proto_obj.Type.Name(
                        nested.field[1].type
                    )
        super().__post_init__()  # call Field -> Message __post_init__

    def get_field_string(self, indent: int = 4) -> str:
        """Construct string representation of this field."""
        name = f"{self.py_name}"
        annotations = f": {self.annotation}"
        betterproto_field_type = (
            f"betterproto.map_field("
            f"{self.proto_obj.number}, betterproto.{self.proto_k_type}, "
            f"betterproto.{self.proto_v_type})"
        )
        return name + annotations + " = " + betterproto_field_type

    @property
    def annotation(self):
        return f"Dict[{self.py_k_type}, {self.py_v_type}]"

    @property
    def repeated(self):
        return False  # maps cannot be repeated


@dataclass
class EnumDefinition(Message):
    """Representation of a proto Enum definition."""

    proto_obj: EnumDescriptorProto = PLACEHOLDER
    entries: List[EnumDefinition.EnumEntry] = PLACEHOLDER

    @dataclass(unsafe_hash=True)
    class EnumEntry:
        """Representation of an Enum entry."""

        name: str
        value: int
        comment: str

    def __post_init__(self):
        # Get entries
        self.entries = [
            self.EnumEntry(
                name=v.name,
                value=v.number,
                comment=get_comment(
                    proto_file=self.proto_file, path=self.path + [2, i]
                ),
            )
            for i, v in enumerate(self.proto_obj.value)
        ]
        super().__post_init__()  # call Message __post_init__

    @property
    def default_value_string(self) -> int:
        """Python representation of the default value for Enums.

        As per the spec, this is the first value of the Enum.
        """
        return str(self.entries[0].value)  # should ALWAYS be int(0)!


@dataclass
class Service(ProtoContentBase):
    parent: ProtoInputFile = PLACEHOLDER
    proto_obj: DescriptorProto = PLACEHOLDER
    path: List[int] = PLACEHOLDER
    methods: List[ServiceMethod] = field(default_factory=list)

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
class ServiceMethod(ProtoContentBase):

    parent: Service
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
        return f"/{self.output_file.input_package}.\
            {self.parent.proto_name}/{self.proto_name}"

    @property
    def py_input_message(self) -> Union[None, Message]:
        """Find the input message object.

        Returns
        -------
        Union[None, Message]
            Method instance representing the input message.
            If not input message could be found or there are no
            input messages, None is returned.
        """
        package, name = parse_source_type_name(self.proto_obj.input_type)

        # Nested types are currently flattened without dots.
        # Todo: keep a fully quantified name in types, that is
        # comparable with method.input_type
        for msg in self.output_file.messages:
            if (
                msg.py_name == self.py_input_message_type
                and msg.output_file.input_package == package
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
            package=self.output_file.input_package,
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
            package=self.output_file.input_package,
            imports=self.output_file.imports,
            source_type=self.proto_obj.output_type,
        ).strip('"')

    @property
    def client_streaming(self) -> bool:
        return self.proto_obj.client_streaming

    @property
    def server_streaming(self) -> bool:
        return self.proto_obj.server_streaming
