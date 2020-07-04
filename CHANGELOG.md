# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

- Versions suffixed with `b*` are in `beta` and can be installed with `pip install --pre betterproto`.

## [2.0.0b1] - 2020-07-04

[Upgrade Guide](./docs/upgrading.md) 

> Several bugfixes and improvements required or will require small breaking changes, necessitating a new version.
> `2.0.0` will be released once the interface is stable.

- Add support for gRPC  and **stream-stream** [#83](https://github.com/danielgtaylor/python-betterproto/pull/83)
- Switch from  to `poetry` for development [#75](https://github.com/danielgtaylor/python-betterproto/pull/75)
- Fix No arguments are generated for stub methods when using import with proto definition 
- Fix two packages with the same name suffix should not cause naming conflict [#25](https://github.com/danielgtaylor/python-betterproto/issues/25)

- Fix Import child package from root [#57](https://github.com/danielgtaylor/python-betterproto/issues/57)
- Fix Import child package from package [#58](https://github.com/danielgtaylor/python-betterproto/issues/58)
- Fix Import parent package from child package [#59](https://github.com/danielgtaylor/python-betterproto/issues/59)
- Fix Import root package from child package [#60](https://github.com/danielgtaylor/python-betterproto/issues/60)
- Fix Import root package from root [#61](https://github.com/danielgtaylor/python-betterproto/issues/61)

- Fix ALL_CAPS message fields are parsed incorrectly. [#11](https://github.com/danielgtaylor/python-betterproto/issues/11)

## [1.2.5] - 2020-04-27

- Add .j2 suffix to python template names to avoid confusing certain build tools [#72](https://github.com/danielgtaylor/python-betterproto/pull/72)

## [1.2.4] - 2020-04-26

- Enforce utf-8 for reading the readme in setup.py [#67](https://github.com/danielgtaylor/python-betterproto/pull/67)
- Only import types from grpclib when type checking [#52](https://github.com/danielgtaylor/python-betterproto/pull/52)
- Improve performance of serialize/deserialize by caching type information of fields in class [#46](https://github.com/danielgtaylor/python-betterproto/pull/46)
- Support using Google's wrapper types as RPC output values [#40](https://github.com/danielgtaylor/python-betterproto/pull/40)
- Fixes issue where protoc did not recognize plugin.py as win32 application [#38](https://github.com/danielgtaylor/python-betterproto/pull/38)
- Fix services using non-pythonified field names [#34](https://github.com/danielgtaylor/python-betterproto/pull/34)
- Add ability to provide metadata, timeout & deadline args to requests [#32](https://github.com/danielgtaylor/python-betterproto/pull/32)

## [1.2.3] - 2020-04-15

- Exclude empty lists from `to_dict` by default [#16](https://github.com/danielgtaylor/python-betterproto/pull/16)
- Add `include_default_values` parameter for `to_dict` [#12](https://github.com/danielgtaylor/python-betterproto/pull/12)
- Fix class names being prepended with duplicates when using protocol buffers that are nested more than once [#21](https://github.com/danielgtaylor/python-betterproto/pull/21)
- Add support for python 3.6 [#30](https://github.com/danielgtaylor/python-betterproto/pull/30)

## [1.2.2] - 2020-01-09

- Mention lack of Proto 2 support in README.
- Fix serialization of constructor parameters [#10](https://github.com/danielgtaylor/python-betterproto/pull/10)
- Fix `casing` parameter propagation [#7](https://github.com/danielgtaylor/python-betterproto/pull/7)

## [1.2.1] - 2019-10-29

- Fix comment indentation bug in rendered gRPC methods.

## [1.2.0] - 2019-10-28

- Generated code output auto-formatting via [Black](https://github.com/psf/black)
- Simplified gRPC helper functions

## [1.1.0] - 2019-10-27

- Better JSON casing support
- Handle field names which clash with Python reserved words
- Better handling of default values from type introspection
- Support for Google Duration & Timestamp types
- Support for Google wrapper types
- Documentation updates

## [1.0.1] - 2019-10-22

- README to the PyPI details page

## [1.0.0] - 2019-10-22

- Initial release

[1.2.5]: https://github.com/danielgtaylor/python-betterproto/compare/v1.2.4...v1.2.5
[1.2.4]: https://github.com/danielgtaylor/python-betterproto/compare/v1.2.3...v1.2.4
[1.2.3]: https://github.com/danielgtaylor/python-betterproto/compare/v1.2.2...v1.2.3
[1.2.2]: https://github.com/danielgtaylor/python-betterproto/compare/v1.2.1...v1.2.2
[1.2.1]: https://github.com/danielgtaylor/python-betterproto/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/danielgtaylor/python-betterproto/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/danielgtaylor/python-betterproto/compare/v1.0.1...v1.1.0
[1.0.1]: https://github.com/danielgtaylor/python-betterproto/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/danielgtaylor/python-betterproto/releases/tag/v1.0.0
