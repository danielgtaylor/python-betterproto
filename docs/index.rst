Welcome to betterproto's documentation!
=======================================

betterproto is a protobuf compiler and interpreter. It improves the experience of using
Protobuf and gRPC in Python, by generating readable, understandable, and idiomatic
Python code, using modern language features.


Features:
~~~~~~~~~

- Generated messages are both binary & JSON serializable
- Messages use relevant python types, e.g. ``Enum``, ``datetime`` and ``timedelta`` objects
- ``async``/``await`` support for gRPC Clients
- Relative imports, mocking protobuf package structure
- Mypy type checkable with full type annotations
- Modern idiomatic python naming conventions

Contents:
~~~~~~~~~

.. toctree::
    :maxdepth: 2

    quick-start
    api
    migrating


If you still can't find what you're looking for, try in one of the following pages:

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
