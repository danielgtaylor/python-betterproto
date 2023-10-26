package betterproto;

import betterproto.nested.NestedOuterClass;
import betterproto.oneof.Oneof;

import com.google.protobuf.CodedInputStream;
import com.google.protobuf.CodedOutputStream;

import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;

public class Tests {
    String path;

    public Tests(String path) {
        this.path = path;
    }

    public void testSingleVarint() throws IOException {
        // Read in the Python-generated single varint file
        FileInputStream inputStream = new FileInputStream(path + "/py_single_varint.out");
        CodedInputStream codedInput = CodedInputStream.newInstance(inputStream);

        int value = codedInput.readUInt32();

        inputStream.close();

        // Write the value back to a file
        FileOutputStream outputStream = new FileOutputStream(path + "/java_single_varint.out");
        CodedOutputStream codedOutput = CodedOutputStream.newInstance(outputStream);

        codedOutput.writeUInt32NoTag(value);

        codedOutput.flush();
        outputStream.close();
    }

    public void testMultipleVarints() throws IOException {
        // Read in the Python-generated multiple varints file
        FileInputStream inputStream = new FileInputStream(path + "/py_multiple_varints.out");
        CodedInputStream codedInput = CodedInputStream.newInstance(inputStream);

        int value1 = codedInput.readUInt32();
        int value2 = codedInput.readUInt32();
        long value3 = codedInput.readUInt64();

        inputStream.close();

        // Write the values back to a file
        FileOutputStream outputStream = new FileOutputStream(path + "/java_multiple_varints.out");
        CodedOutputStream codedOutput = CodedOutputStream.newInstance(outputStream);

        codedOutput.writeUInt32NoTag(value1);
        codedOutput.writeUInt64NoTag(value2);
        codedOutput.writeUInt64NoTag(value3);

        codedOutput.flush();
        outputStream.close();
    }

    public void testSingleMessage() throws IOException {
        // Read in the Python-generated single message file
        FileInputStream inputStream = new FileInputStream(path + "/py_single_message.out");
        CodedInputStream codedInput = CodedInputStream.newInstance(inputStream);

        Oneof.Test message = Oneof.Test.parseFrom(codedInput);

        inputStream.close();

        // Write the message back to a file
        FileOutputStream outputStream = new FileOutputStream(path + "/java_single_message.out");
        CodedOutputStream codedOutput = CodedOutputStream.newInstance(outputStream);

        message.writeTo(codedOutput);

        codedOutput.flush();
        outputStream.close();
    }

    public void testMultipleMessages() throws IOException {
        // Read in the Python-generated multi-message file
        FileInputStream inputStream = new FileInputStream(path + "/py_multiple_messages.out");

        Oneof.Test oneof = Oneof.Test.parseDelimitedFrom(inputStream);
        NestedOuterClass.Test nested = NestedOuterClass.Test.parseDelimitedFrom(inputStream);

        inputStream.close();

        // Write the messages back to a file
        FileOutputStream outputStream = new FileOutputStream(path + "/java_multiple_messages.out");

        oneof.writeDelimitedTo(outputStream);
        nested.writeDelimitedTo(outputStream);

        outputStream.flush();
        outputStream.close();
    }

    public void testInfiniteMessages() throws IOException {
        // Read in as many messages as are present in the Python-generated file and write them back
        FileInputStream inputStream = new FileInputStream(path + "/py_infinite_messages.out");
        FileOutputStream outputStream = new FileOutputStream(path + "/java_infinite_messages.out");

        Oneof.Test current = Oneof.Test.parseDelimitedFrom(inputStream);
        while (current != null) {
            current.writeDelimitedTo(outputStream);
            current = Oneof.Test.parseDelimitedFrom(inputStream);
        }

        inputStream.close();
        outputStream.flush();
        outputStream.close();
    }
}
