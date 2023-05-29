# Standard Tests Development Guide

Standard test cases are found in [betterproto/tests/inputs](inputs), where each subdirectory represents a testcase, that is verified in isolation.

```
inputs/
   bool/
   double/
   int32/
   ...
```

## Test case directory structure

Each testcase has a `<name>.proto` file with a message called `Test`, and optionally a matching `.json` file and a custom test called `test_*.py`.

```bash
bool/
  bool.proto
  bool.json     # optional
  test_bool.py  # optional
```

### proto

`<name>.proto` &mdash; *The protobuf message to test*

```protobuf
syntax = "proto3";

message Test {
    bool value = 1;
}
```

You can add multiple `.proto` files to the test case, as long as one file matches the directory name. 

### json

`<name>.json` &mdash; *Test-data to validate the message with*

```json
{
  "value": true
}
```

### pytest

`test_<name>.py` &mdash; *Custom test to validate specific aspects of the generated class*

```python
from tests.output_betterproto.bool.bool import Test

def test_value():
    message = Test()
    assert not message.value, "Boolean is False by default"
```

## Standard tests

The following tests are automatically executed for all cases:

- [x] Can the generated python code be imported?
- [x] Can the generated message class be instantiated?
- [x] Is the generated code compatible with the Google's `grpc_tools.protoc` implementation?
  - _when `.json` is present_ 

## Environment setup

Before running the tests, you will need to do the following:

```sh
# Shortcut for running poe
alias poe="poetry run poe"

# Install protoc-gen-python_betterproto to your path
poetry install --extras=compiler

# (opational) Increase the file limit for generating code
ulimit -n 4096
```

## Running the tests

- `poe generate`  
  This generates:
  - `betterproto/tests/output_betterproto` &mdash; *the plugin generated python classes*
  - `betterproto/tests/output_reference` &mdash; *reference implementation classes*
- `poe test`

## Intentionally Failing tests

The standard test suite includes tests that fail by intention. These tests document known bugs and missing features that are intended to be corrected in the future.

When running `pytest`, they show up as `x` or  `X` in the test results.

```
betterproto/tests/test_inputs.py ..x...x..x...x.X........xx........x.....x.......x.xx....x...................... [ 84%]
```

- `.` &mdash; PASSED
- `x` &mdash; XFAIL: expected failure
- `X` &mdash; XPASS: expected failure, but still passed

Test cases marked for expected failure are declared in [inputs/config.py](inputs/config.py)