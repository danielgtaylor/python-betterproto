#!/usr/bin/env python
import os

# Force pure-python implementation instead of C++, otherwise imports
# break things because we can't properly reset the symbol database.
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"


from betterproto.tests.util import get_directories, protoc_plugin, protoc_reference, root_path

def main():
    os.chdir(root_path)
    test_cases_directory = os.path.join(root_path, 'inputs')
    test_case = get_directories(test_cases_directory)

    for test_case_name in test_case:
        test_case_path = os.path.join(test_cases_directory, test_case_name)

        case_reference_output_dir = os.path.join(root_path, 'output_reference', test_case_name)
        case_plugin_output_dir = os.path.join(root_path, 'output_betterproto', test_case_name)

        print(f'Generating output for {test_case_name}')
        os.makedirs(case_reference_output_dir, exist_ok=True)
        os.makedirs(case_plugin_output_dir, exist_ok=True)

        protoc_reference(test_case_path, case_reference_output_dir)
        protoc_plugin(test_case_path, case_plugin_output_dir)


if __name__ == "__main__":
    main()
