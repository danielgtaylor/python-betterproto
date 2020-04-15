# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[unreleased]: https://github.com/danielgtaylor/python-betterproto/compare/v1.2.2...HEAD
[1.2.2]: https://github.com/danielgtaylor/python-betterproto/compare/v1.2.1...v1.2.2
[1.2.1]: https://github.com/danielgtaylor/python-betterproto/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/danielgtaylor/python-betterproto/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/danielgtaylor/python-betterproto/compare/v1.0.1...v1.1.0
[1.0.1]: https://github.com/danielgtaylor/python-betterproto/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/danielgtaylor/python-betterproto/releases/tag/v1.0.0
