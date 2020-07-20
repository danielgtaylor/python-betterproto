Migrating Guide
===============

Google's protocolbuffers
------------------------

.. TODO notes about compatibility



[1.2.5] to [2.0.0b1]
--------------------

Updated package structures
~~~~~~~~~~~~~~~~~~~~~~~~~~

Generated code now strictly follows the *package structure* of the ``.proto`` files.
Consequently ``.proto`` files without a package will be combined in a single ``__init__.py`` file.
To avoid overwriting existing ``__init__.py`` files, its best to compile into a dedicated subdirectory.

Upgrading:

- Remove your previously compiled ``.py`` files.
- Create a new *empty* directory, e.g. ``generated`` or ``lib/generated/proto`` etc.
- Regenerate your python files into this directory
- Update import statements, e.g. ``import ExampleMessage from generated``