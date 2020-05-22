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

Each testcase has a `<name>.proto` file with a message called `Test`, a matching `.json` file and optionally a custom test file called `test_*.py`.

```bash
bool/
  bool.proto
  bool.json
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
from betterproto.tests.output_betterproto.bool.bool import Test

def test_value():
    message = Test()
    assert not message.value, "Boolean is False by default"
```

## Standard tests

The following tests are automatically executed for all cases:

- [x] Can the generated python code imported?
- [x] Can the generated message class be instantiated?
- [x] Is the generated code compatible with the Google's `grpc_tools.protoc` implementation?

## Running the tests

- `pipenv run generate`
  This generates
  - `betterproto/tests/output_betterproto` &mdash; *the plugin generated python classes*
  - `betterproto/tests/output_reference` &mdash; *reference implementation classes*
- `pipenv run test`

