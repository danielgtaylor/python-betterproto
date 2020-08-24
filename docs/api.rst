.. currentmodule:: betterproto

API reference
=============

The following document outlines betterproto's api. **None** of these classes should be
extended by the user manually.


Message
--------

.. autoclass:: betterproto.Message
    :members:
    :special-members: __bytes__


.. automethod:: betterproto.serialized_on_wire

.. automethod:: betterproto.which_one_of


Enumerations
-------------

.. autoclass:: betterproto.Enum()
    :members:


.. autoclass:: betterproto.Casing()
    :members:
