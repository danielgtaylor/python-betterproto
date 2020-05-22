#!/usr/bin/env python
import os
import sys
from typing import Set

from betterproto.tests.util import get_directories, inputs_path, output_path_betterproto, output_path_reference, \
    protoc_plugin, protoc_reference

# Force pure-python implementation instead of C++, otherwise imports
# break things because we can't properly reset the symbol database.
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"


def generate(whitelist: Set[str]):
    path_whitelist = {os.path.realpath(e) for e in whitelist if os.path.exists(e)}
    name_whitelist = {e for e in whitelist if not os.path.exists(e)}

    test_case_names = set(get_directories(inputs_path))

    for test_case_name in test_case_names:
        test_case_path = os.path.join(inputs_path, test_case_name)

        is_path_whitelisted = path_whitelist and os.path.realpath(test_case_path) in path_whitelist
        is_name_whitelisted = name_whitelist and test_case_name in name_whitelist

        if whitelist and not is_path_whitelisted and not is_name_whitelisted:
            continue

        case_output_dir_reference = os.path.join(output_path_reference, test_case_name)
        case_output_dir_betterproto = os.path.join(output_path_betterproto, test_case_name)

        print(f'Generating output for {test_case_name}')
        os.makedirs(case_output_dir_reference, exist_ok=True)
        os.makedirs(case_output_dir_betterproto, exist_ok=True)

        protoc_reference(test_case_path, case_output_dir_reference)
        protoc_plugin(test_case_path, case_output_dir_betterproto)


HELP = "\n".join([
    'Usage: python generate.py',
    '       python generate.py [DIRECTORIES or NAMES]',
    'Generate python classes for standard tests.',
    '',
    'DIRECTORIES    One or more relative or absolute directories of test-cases to generate classes for.',
    '               python generate.py inputs/bool inputs/double inputs/enum',
    '',
    'NAMES          One or more test-case names to generate classes for.',
    '               python generate.py bool double enums'
])


def main():
    if sys.argv[1] in ('-h', '--help'):
        print(HELP)
        return
    whitelist = set(sys.argv[1:])

    generate(whitelist)


if __name__ == "__main__":
    main()
