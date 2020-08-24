Welcome to betterproto's documentation!
=======================================

betterproto is a protobuf compiler and interpreter. It improves the experience of using
Protobuf and gRPC in Python, by generating readable, understandable, and idiomatic
Python code, using modern language features.


Features:
~~~~~~~~~

- Generated messages are both binary & JSON serializable
- Messages use relevant python types, e.g. ``Enum``, ``datetime`` and ``timedelta``
  objects
- ``async``/``await`` support for gRPC Clients
- Generates modern idiomatic python code
  - Easy to understand and read due to the use of dataclasses
  - Fully typed-hinted/annotated
  - Looks like Python code built for Python rather than a 1:1 port of C++ or Java
  - Standard snake case naming conventions and use of magic methods e.g.
    :meth:`betteproto.Message.__bytes__()`

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
