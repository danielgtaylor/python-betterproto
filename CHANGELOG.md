# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

- Versions suffixed with `b*` are in `beta` and can be installed with `pip install --pre betterproto`.

## [2.0.0b6] - 2023-06-25

- **Breaking**: the minimum Python version has been bumped to `3.7` [#444](https://github.com/danielgtaylor/python-betterproto/pull/444)

- Support generating [Pydantic dataclasses](https://docs.pydantic.dev/latest/usage/dataclasses). 
  Pydantic dataclasses are are drop-in replacement for dataclasses in the standard library that additionally supports validation.
  Pass `--python_betterproto_opt=pydantic_dataclasses` to enable this feature.
  Refer to [#406](https://github.com/danielgtaylor/python-betterproto/pull/406)
  and [README.md](https://github.com/danielgtaylor/python-betterproto#generating-pydantic-models) for more information.
  
- Added support for `@generated` marker [#382](https://github.com/danielgtaylor/python-betterproto/pull/382)
- Pull down the `include_default_values` argument to `to_json()` [#405](https://github.com/danielgtaylor/python-betterproto/pull/405)
- Pythonize input_type name in py_input_message [#436](https://github.com/danielgtaylor/python-betterproto/pull/436)
- Widen `from_dict()` to accept any `Mapping` [#451](https://github.com/danielgtaylor/python-betterproto/pull/451)
- Replace `pkg_resources` with `importlib` [#462](https://github.com/danielgtaylor/python-betterproto/pull/462)
  
- Fix typechecker compatiblity checks in server streaming methods [#413](https://github.com/danielgtaylor/python-betterproto/pull/413)
- Fix "empty-valued" repeated fields not being serialised [#417](https://github.com/danielgtaylor/python-betterproto/pull/417)
- Fix `dict` encoding for timezone-aware `datetimes` [#468](https://github.com/danielgtaylor/python-betterproto/pull/468)
- Fix `to_pydict()` serialization for optional fields [#495](https://github.com/danielgtaylor/python-betterproto/pull/495)
- Handle empty value objects properly [#481](https://github.com/danielgtaylor/python-betterproto/pull/481)
  
## [2.0.0b5] - 2022-08-01

- **Breaking**: Client and Service Stubs no longer pack and unpack the input message fields as parameters [#331](https://github.com/danielgtaylor/python-betterproto/pull/311)

    Update your client calls and server handlers as follows:

    Clients before:

    ```py
    response = await service.echo(value="hello", extra_times=1)
    ```

    Clients after:

    ```py
    response = await service.echo(EchoRequest(value="hello", extra_times=1))
    ```

    Servers before:

    ```py
    async def echo(self, value: str, extra_times: int) -> EchoResponse: ...
    ```

    Servers after:

    ```py
    async def echo(self, echo_request: EchoRequest) -> EchoResponse:
        # Use echo_request.value
        # Use echo_request.extra_times
        ...
    ```

- Add `to/from_pydict()` for `Message` [#203](https://github.com/danielgtaylor/python-betterproto/pull/203)
- Format field comments also as docstrings [#304](https://github.com/danielgtaylor/python-betterproto/pull/304)
- Implement `__deepcopy__` for `Message` [#339](https://github.com/danielgtaylor/python-betterproto/pull/339)
- Run isort on compiled code [#355](https://github.com/danielgtaylor/python-betterproto/pull/355)
- Expose timeout, deadline and metadata parameters from grpclib [#352](https://github.com/danielgtaylor/python-betterproto/pull/352)
- Make `Message.__getattribute__` invisible to type checkers [#359](https://github.com/danielgtaylor/python-betterproto/pull/359)

- Fix map field edge-case [#254](https://github.com/danielgtaylor/python-betterproto/pull/254)
- Fix message text in `NotImplementedError` [#325](https://github.com/danielgtaylor/python-betterproto/pull/325)
- Fix `Message.from_dict()` in the presence of optional datetime fields [#329](https://github.com/danielgtaylor/python-betterproto/pull/329)
- Support Jinja2 3.0 to prevent version conflicts [#330](https://github.com/danielgtaylor/python-betterproto/pull/330)
- Fix overwriting top level `__init__.py` [#337](https://github.com/danielgtaylor/python-betterproto/pull/337)
- Remove deprecation warnings when fields are initialised with non-default values [#348](https://github.com/danielgtaylor/python-betterproto/pull/348)
- Ensure nested class names are converted to PascalCase [#353](https://github.com/danielgtaylor/python-betterproto/pull/353)
- Fix `Message.to_dict()` mutating the underlying Message [#378](https://github.com/danielgtaylor/python-betterproto/pull/378)
- Fix some parameters being missing from services [#381](https://github.com/danielgtaylor/python-betterproto/pull/381)

## [2.0.0b4] - 2022-01-03

- **Breaking**: the minimum Python version has been bumped to `3.6.2`

- Always add `AsyncIterator` to imports if there are services [#264](https://github.com/danielgtaylor/python-betterproto/pull/264)
- Allow parsing of messages from `ByteStrings` [#266](https://github.com/danielgtaylor/python-betterproto/pull/266)
- Add support for proto3 optional [#281](https://github.com/danielgtaylor/python-betterproto/pull/281)

- Fix compilation of fields with names identical to builtin types [#294](https://github.com/danielgtaylor/python-betterproto/pull/294)
- Fix default values for enum service args [#299](https://github.com/danielgtaylor/python-betterproto/pull/299)

## [2.0.0b3] - 2021-04-07

- Generate grpclib service stubs [#170](https://github.com/danielgtaylor/python-betterproto/pull/170)
- Add \_\_version\_\_ attribute to package [#134](https://github.com/danielgtaylor/python-betterproto/pull/134)
- Use betterproto generated messages in the plugin [#161](https://github.com/danielgtaylor/python-betterproto/pull/161)
- Sort the list of sources in generated file headers [#164](https://github.com/danielgtaylor/python-betterproto/pull/164)
- Micro-optimization: use tuples instead of lists for conditions [#228](https://github.com/danielgtaylor/python-betterproto/pull/228)
- Improve datestring parsing [#213](https://github.com/danielgtaylor/python-betterproto/pull/213)

- Fix serialization of repeated fields with empty messages [#180](https://github.com/danielgtaylor/python-betterproto/pull/180)
- Fix compilation of fields named 'bytes' or 'str' [#226](https://github.com/danielgtaylor/python-betterproto/pull/226)
- Fix json serialization of infinite and nan floats/doubles [#215](https://github.com/danielgtaylor/python-betterproto/pull/215)
- Fix template bug resulting in empty \_\_post_init\_\_ methods [#162](https://github.com/danielgtaylor/python-betterproto/pull/162)
- Fix serialization of zero-value messages in a oneof group [#176](https://github.com/danielgtaylor/python-betterproto/pull/176)
- Fix missing typing and datetime imports [#183](https://github.com/danielgtaylor/python-betterproto/pull/183)
- Fix code generation for empty services [#222](https://github.com/danielgtaylor/python-betterproto/pull/222)
- Fix Message.to_dict and from_dict handling of repeated timestamps and durations [#211](https://github.com/danielgtaylor/python-betterproto/pull/211)
- Fix incorrect routes in generated client when service is not in a package [#177](https://github.com/danielgtaylor/python-betterproto/pull/177)

## [2.0.0b2] - 2020-11-24

- Add support for deprecated message and fields [#126](https://github.com/danielgtaylor/python-betterproto/pull/126)
- Add support for recursive messages [#130](https://github.com/danielgtaylor/python-betterproto/pull/130)
- Add support for `bool(Message)` [#142](https://github.com/danielgtaylor/python-betterproto/pull/142)
- Improve support for Python 3.9 [#140](https://github.com/danielgtaylor/python-betterproto/pull/140) [#173](https://github.com/danielgtaylor/python-betterproto/pull/173)
- Improve keyword sanitisation for generated code [#137](https://github.com/danielgtaylor/python-betterproto/pull/137)

- Fix missing serialized_on_wire when message contains only lists [#81](https://github.com/danielgtaylor/python-betterproto/pull/81)
- Fix circular dependencies [#100](https://github.com/danielgtaylor/python-betterproto/pull/100)
- Fix to_dict enum fields when numbering is not consecutive [#102](https://github.com/danielgtaylor/python-betterproto/pull/102)
- Fix argument generation for stub methods when using `import` with proto definition [#103](https://github.com/danielgtaylor/python-betterproto/pull/103)
- Fix missing async/await keywords when casing [#104](https://github.com/danielgtaylor/python-betterproto/pull/104)
- Fix mutable default arguments in generated code [#105](https://github.com/danielgtaylor/python-betterproto/pull/105)
- Fix serialisation of default values in oneofs when calling to_dict() or to_json() [#110](https://github.com/danielgtaylor/python-betterproto/pull/110)
- Fix static type checking for grpclib client [#124](https://github.com/danielgtaylor/python-betterproto/pull/124)
- Fix python3.6 compatibility issue with dataclasses [#124](https://github.com/danielgtaylor/python-betterproto/pull/124)
- Fix handling of trailer-only responses [#127](https://github.com/danielgtaylor/python-betterproto/pull/127)

- Refactor plugin.py to use modular dataclasses in tree-like structure to represent parsed data [#121](https://github.com/danielgtaylor/python-betterproto/pull/121)
- Refactor template compilation logic [#136](https://github.com/danielgtaylor/python-betterproto/pull/136)

- Replace use of platform provided protoc with development dependency on grpcio-tools [#107](https://github.com/danielgtaylor/python-betterproto/pull/107)
- Switch to using `poe` from `make` to manage project development tasks [#118](https://github.com/danielgtaylor/python-betterproto/pull/118)
- Improve CI platform coverage [#128](https://github.com/danielgtaylor/python-betterproto/pull/128)

## [2.0.0b1] - 2020-07-04

[Upgrade Guide](./docs/upgrading.md)

> Several bugfixes and improvements required or will require small breaking changes, necessitating a new version.
> `2.0.0` will be released once the interface is stable.

- Add support for gRPC  and **stream-stream** [#83](https://github.com/danielgtaylor/python-betterproto/pull/83)
- Switch from `pipenv` to `poetry` for development [#75](https://github.com/danielgtaylor/python-betterproto/pull/75)
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
