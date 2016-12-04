Available Filters
=================
These filters are included in the Filters library.
You can also write your own filters.

Simple Filters
--------------
Simple filters operate on one value at a time.
This is in contrast to :ref:`Complex Filters <complex-filters>`, which operate
on collections of values.

.. autoclass:: filters.Array
.. autoclass:: filters.Base64Decode
.. autoclass:: filters.ByteArray
.. autoclass:: filters.ByteString
.. autoclass:: filters.CaseFold
.. autoclass:: filters.Choice
.. autoclass:: filters.Date
.. autoclass:: filters.Datetime
.. autoclass:: filters.Empty
.. autoclass:: filters.Int
.. autoclass:: filters.IpAddress
.. autoclass:: filters.JsonDecode
.. autoclass:: filters.Length
.. autoclass:: filters.Max
.. autoclass:: filters.MaxBytes
.. autoclass:: filters.MaxLength
.. autoclass:: filters.Min
.. autoclass:: filters.MinLength
.. autoclass:: filters.NoOp
.. autoclass:: filters.NotEmpty
.. autoclass:: filters.Optional
.. autoclass:: filters.Regex
.. autoclass:: filters.Required
.. autoclass:: filters.Round
.. autoclass:: filters.Split
.. autoclass:: filters.Strip
.. autoclass:: filters.Type
.. autoclass:: filters.Unicode
.. autoclass:: filters.Uuid

.. _complex-filters:

Complex Filters
---------------
Complex filters are used to apply other filters to collections of values.

.. autoclass:: filters.FilterMapper
.. autoclass:: filters.FilterRepeater
