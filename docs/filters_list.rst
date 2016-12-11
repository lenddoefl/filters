=================
Available Filters
=================
These filters are included in the Filters library.
You can also :doc:`write your own filters </writing_filters>`.

--------------
Simple Filters
--------------
Simple filters operate on one value at a time.
This is in contrast to :ref:`Complex Filters <complex-filters>`, which operate
on collections of values.

String Filters
--------------
These filters are designed to operate on (or convert to) string values.

*Important:* to ensure consistent behavior between Python 2 and Python 3,
string filters only accept unicode strings, unless otherwise noted.

:py:class:`filters.Base64Decode`
   Decodes a string that is encoded using
   `Base 64 <https://en.wikipedia.org/wiki/Base64>`_.

   Automatically handles URL-safe variant and incorrect/missing padding.

:py:class:`filters.ByteString`
   Converts a value into a byte string (``bytes`` in Python 3, ``str`` in Python
   2).

   By default, this filter encodes the result using UTF-8, but you can change
   this via the ``encoding`` parameter in the filter initializer.

:py:class:`filters.CaseFold`
   Applies
   `case folding <https://en.wikipedia.org/wiki/Letter_case#Case_folding>`_ to
   a string value.

:py:class:`filters.Choice`
   Requires the incoming value to match one of the values specified in the
   filter's initializer.

   Note that the comparison is case sensitive; chain this filter with
   :py:class:`filters.CaseFold` for case-insensitive comparison.

:py:class:`filters.Date`
   Interprets a string as a date.  The result is a ``datetime.date`` instance.

   If the incoming value appears to be a datetime, it is first converted to
   UTC.  In some cases, this can make the resulting date appear to be off by 1
   day.

:py:class:`filters.Datetime`
   Interprets a string as a datetime.  The result is a ``datetime.datetime``
   instance with ``tzinfo=utc``.

   If the incoming value includes a timezone indicator, it is automatically
   converted to UTC.  Otherwise, it is assumed to already be UTC (this can be
   configured via the filter initializer).

:py:class:`filters.IpAddress`
   Validates the incoming value as an IP address.

   By default, this filter only accepts IPv4 addresses, but you can configure
   the filter to also/only accept IPv6 addresses via its initializer.

:py:class:`filters.JsonDecode`
   Decodes a string that is JSON-encoded.

   Note that this filter can be chained with other filters.  For example, you
   can use ``f.JsonDecode | f.FilterMapper(...)`` to apply filters to a JSON-
   encoded dict.

:py:class:`filters.MaxBytes`
   Truncates a string to a max number of bytes, with support for multibyte
   encodings.

:py:class:`filters.Regex`
   Executes a regular expression against a string value.  The regex must match
   in order for the string to be considered valid.

   This filter returns an array of matches.

   Note: Groups are not included in the result.

:py:class:`filters.Split`
   Uses a regular expression to split a string value into chunks.

:py:class:`filters.Strip`
   Uses regular expressions to remove characters from the start and/or end of
   a string value.

:py:class:`filters.Unicode`
   Converts a value to a unicode string (``str`` in Python 3, ``unicode`` in
   Python 2).

   By default the filter also applies the following transformations:

      - Convert to `NFC form <https://en.wikipedia.org/wiki/Unicode_equivalence>`_.
      - Remove non-printable characters.
      - Normalize line endings.

   If desired, you can disable these extra transformations via the filter
   initializer.

:py:class:`filters.Uuid`
   Converts a string value into a :py:class:`uuid.UUID` object.

   By default, any UUID version is allowed, but you can specify the required
   version in the filter initializer.

Number Filters
--------------
These filters are designed to operate on (or convert to) numeric types.

:py:class:`filters.Int`
   Interprets the incoming value as an int.

   Strings and other compatible types will be converted transparently.
   Floats are only valid if they have an empty fpart.

:py:class:`filters.Max`
   Requires that the value be less than [or equal to] the value specified in
   the filter initializer.

:py:class:`filters.Min`
   Requires that the value be greater than [or equal to] the value specified in
   the filter initializer.

:py:class:`filters.Round`
   Rounds the incoming value to the nearest integer or fraction specified in
   the filter initializer.

   By default, the result is always a ``decimal.Decimal`` instance, to avoid
   issues with
   `floating-point precision <https://en.wikipedia.org/wiki/Floating_point#Accuracy_problems>`_.

Collection Filters
------------------
These filters are designed to operate on collections of values.
Most of these filters can also operate on strings, except where noted.

:py:class:`filters.ByteArray`
   Attempts to convert a value into a ``bytearray``.

:py:class:`filters.Empty`
   Requires that a value have a length of zero.

   Values that are not ``Sized`` (i.e., do not have ``__len__``) are considered
   to be not empty.  In particular, this means that ``0`` and ``False`` are
   *not* considered empty in this context.

:py:class:`filters.Length`:
   Requires that a value's length matches the value specified in the filter
   initializer.

   Values that are not ``Sized`` (i.e., do not have ``__len__``) automatically
   fail.

:py:class:`filters.MaxLength`:
   Requires that a value's length is less than or equal to the value specified
   in the filter initializer.

   Values that are not ``Sized`` (i.e., do not have ``__len__``) automatically
   fail.

:py:class:`filters.MinLength`:
   Requires that a value's length is greater than or equal to the value
   specified in the filter initializer.

   Values that are not ``Sized`` (i.e., do not have ``__len__``) automatically
   fail.

:py:class:`filters.NotEmpty`:
   Requires that a value a length greater than zero.

   Values that are not ``Sized`` (i.e., do not have ``__len__``) are considered
   to be not empty.  In particular, this means that ``0`` and ``False`` are
   *not* considered empty in this context.

   **Important:** ``None`` always passes this filter.
   Use :py:class:`filters.Required` to reject ``None``.

   Examples::

      # Convert to unicode, reject empty strings, but allow `None`.
      f.Unicode | f.NotEmpty

      # Convert to unicode, reject empty strings and `None`.
      f.Unicode | f.Required


Miscellaneous Filters
---------------------
These filters do various things that defy categorization.

:py:class:`filters.Array`
   Requires that a value is a ``Sequence`` and not a string.

   For example, ``list`` or any class that extends ``typing.Sequence`` will
   pass, but any string type (or subclass thereof) will fail.

:py:class:`filters.NoOp`
   This filter returns the incoming value unmodified.

   It can be useful in cases where you need a function to return a filter
   instance, even in cases where no filtering is needed.

   Note that in most contexts, you can safely substitute ``None`` for
   :py:class:`filters.NoOp`.

:py:class:`filters.Optional`
   Provides a default value that will be returned if the incoming value is
   empty (has a length of zero or is ``None``).

   Values that are not ``Sized`` (i.e., do not have ``__len__``) are considered
   to be not empty.  In particular, this means that ``0`` and ``False`` are
   *not* considered empty in this context.

   This filter is usually appended to the end of a chain.  For example:

   .. code-block:: python

      # If the incoming value is `None`, replace it with 't'.
      f.Unicode | f.NotEmpty | f.Choice({'t', 'f'}) | Optional('t')

:py:class:`filters.Required`
   Basically the same as :py:class:`NotEmpty`, except it also rejects ``None``.

   This filter is the only exception to the "``None`` always passes" rule.

   Examples:

   .. code-block:: python

      # Convert to unicode, reject empty strings, but allow `None`.
      f.Unicode | f.NotEmpty

      # Convert to unicode, reject empty strings and `None`.
      f.Unicode | f.Required

:py:class:`filters.Type`
   Requires that the incoming value have the type specified in the filter
   initializer.

   You can specify a tuple of types, the same as you would for ``isinstance``.

   By default, the filter permits subclasses, but you can configure it via the
   initializer to require an exact type match.

.. _complex-filters:

---------------
Complex Filters
---------------
Complex filters are used to apply other filters to collections of values.

These filters are covered in more detail in :doc:`/complex_filters`.

:py:class:`filters.FilterMapper`
   Applies filters to an incoming mapping (e.g., ``dict``).

   When initializing the filter, you must provide a dict that tells the
   FilterMapper which filters to apply to each key in the incoming dict.

   By default, the FilterMapper will ignore missing/unexpected keys, but you
   can configure this via the filter initializer as well.

   This filter is often chained with :py:class:`filters.JsonDecode`.

:py:class:`filters.FilterRepeater`
   Applies filters to every value in an incoming iterable (e.g., ``list``).

   ``FilterRepeater`` can also process mappings (e.g., ``dict``); it will apply
   the filters to every value in the mapping, preserving the keys.
