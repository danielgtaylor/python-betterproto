.. currentmodule:: bananaproto

API reference
=============

The following document outlines bananaproto's api. **None** of these classes should be
extended by the user manually.


Message
--------

.. autoclass:: bananaproto.Message
    :members:
    :special-members: __bytes__, __bool__


.. autofunction:: bananaproto.serialized_on_wire

.. autofunction:: bananaproto.which_one_of


Enumerations
-------------

.. autoclass:: bananaproto.Enum()
    :members:


.. autoclass:: bananaproto.Casing()
    :members:
