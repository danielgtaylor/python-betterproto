package betterproto;

import java.io.IOException;

public class CompatibilityTest {
    public static void main(String[] args) throws IOException {
        if (args.length < 2)
            throw new RuntimeException("Attempted to run without the required arguments.");
        else if (args.length > 2)
            throw new RuntimeException(
                    "Attempted to run with more than the expected number of arguments (>1).");

        Tests tests = new Tests(args[1]);

        switch (args[0]) {
            case "single_varint":
                tests.testSingleVarint();
                break;

            case "multiple_varints":
                tests.testMultipleVarints();
                break;

            case "single_message":
                tests.testSingleMessage();
                break;

            case "multiple_messages":
                tests.testMultipleMessages();
                break;

            case "infinite_messages":
                tests.testInfiniteMessages();
                break;

            default:
                throw new RuntimeException(
                        "Attempted to run with unknown argument '" + args[0] + "'.");
        }
    }
}
