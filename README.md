# Better Protobuf / gRPC Support for Python

This project aims to provide an improved experience when using Protobuf / gRPC in a modern Python environment by making use of modern language features and generating readable, understandable code. It will not support legacy features or environments. The following are supported:

- Protobuf 3 & gRPC code generation
  - Both binary & JSON serialization is built-in
- Python 3.7+
  - Enums
  - Dataclasses
  - `async`/`await`
  - Relative imports
  - Mypy type checking

This project is heavily inspired by, and borrows functionality from:

- https://github.com/eigenein/protobuf/
- https://github.com/vmagamedov/grpclib

## TODO

- [x] Fixed length fields
  - [x] Packed fixed-length
- [x] Zig-zag signed fields (sint32, sint64)
- [x] Don't encode zero values for nested types
- [x] Enums
- [x] Repeated message fields
- [x] Maps
  - [x] Maps of message fields
- [ ] Support passthrough of unknown fields
- [ ] Refs to nested types
- [ ] Imports in proto files
- [ ] Well-known Google types
- [ ] JSON that isn't completely naive.
- [ ] Async service stubs
- [ ] Python package
- [ ] Cleanup!
