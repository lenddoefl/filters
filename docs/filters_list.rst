Available Filters
=================
These filters are included in the Filters library.
You can also :doc:`write your own filters </writing_filters>`.

Simple Filters
--------------
Simple filters operate on one value at a time.
This is in contrast to :ref:`Complex Filters <complex-filters>`, which operate
on collections of values.

String Filters
^^^^^^^^^^^^^^
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

:py:class:`filters.NamedTuple`
   Converts the incoming value into a named tuple

   Initialize this filter with the type of named tuple that you want to use for
   conversions.

   You can also provide an optional filter map, which will be applied to the
   values in the resulting named tuple.

   Example:

   .. code-block:: python

      Color = namedtuple('Color', ('r', 'g', 'b'))

      filter_chain = f.NamedTuple(Color, {
          'r': f.Required | f.Int | f.Min(0) | f.Max(255),
          'g': f.Required | f.Int | f.Min(0) | f.Max(255),
          'b': f.Required | f.Int | f.Min(0) | f.Max(255),
      })

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
^^^^^^^^^^^^^^
These filters are designed to operate on (or convert to) numeric types.

:py:class:`filters.Decimal`
   Interprets the incoming value as a ``decimal.Decimal``.

   Virtually any value that can be passed to ``decimal.Decimal.__init__`` is
   accepted (including scientific notation), with a few exceptions:

      - Non-finite values (e.g., ``NaN``, ``+Inf``, etc.) are not allowed.
      - Tuple/list values (e.g., ``(0, (4, 2), -1)``) are allowed by default,
        but you can disallow these values in the filter initializer.

   The filter initializer also accepts a parameter to set max precision.  If
   specified, the resulting values will be *truncated* to the specified number
   of decimal places.

   If you want to round to the specified precision instead, chain the filter
   with :py:class:`filters.Round`.

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
^^^^^^^^^^^^^^^^^^
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
^^^^^^^^^^^^^^^^^^^^^
These filters do various things that defy categorization.

:py:class:`filters.Array`
   Requires that a value is a ``Sequence`` and not a string.

   For example, ``list`` or any class that extends ``typing.Sequence`` will
   pass, but any string type (or subclass thereof) will fail.

:py:class:`filters.Call`
   Calls an arbitrary function on the incoming value.

   This filter is almost always inferior to
   :doc:`creating a custom filter </writing_filters>`, but it can be a useful
   way to quickly inject a function into a filter workflow to see if it will
   work.

   .. important::
      The function must raise a :py:class:`filters.FilterError` to indicate that
      the incoming value is not valid.

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

:py:class:`filters.FilterSwitch`
   Conditionally invokes a filter based on the output of a function.

   ``FilterSwitch`` takes 2-3 parameters:

   - ``getter: Callable[[Any], Hashable]`` - a function that extracts the
     comparison value from the incoming value.  Whatever this function returns
     will be matched against the keys in ``cases``.
   - ``cases: Mapping[Hashable, FilterCompatible]`` - a mapping of valid
     comparison values and their corresponding filters.
   - ``default: Optional[FilterCompatible]`` - if specified, this is the filter
     that will be used if the comparison value doesn't match any cases.  If not
     specified, then the incoming value will be considered invalid if the
     comparison value doesn't match any cases.

   Example of a ``FilterSwitch`` that selects the correct filter to use based
   upon the incoming value's ``name`` value:

   .. code-block:: py

      switch = f.FilterSwitch(
          # This function will extract the comparison value.
          getter=lambda value: value['name'],

          # These are the cases that the comparison value might
          # match.
          cases={
              'price': f.FilterMapper({'value': f.Int | f.Min(0)}),
              'color': f.FilterMapper({'value': f.Choice({'r', 'g', 'b'})}),
              # etc.
          },

          # This is the filter that will be used if none of the cases match.
          default=f.FilterMapper({'value': f.Unicode}),
      )

      # Applies the 'price' filter:
      switch.apply({'name': price, 'value': 42})

      # Applies the 'color' filter:
      switch.apply({'name': color, 'value': 'b'})

      # Applies the default filter:
      switch.apply({'name': 'mfg', 'value': 'Acme Widget Co.'})

Extensions
==========
The following filters are provided by the
:doc:`Extensions framework </extensions>`.

Note that extension filters are located in a different namespace; use
``filters.ext`` to use them instead of ``filters``.  For example:

.. code:: python

   import filters as f

   # Standard filter
   f.Unicode().apply('foo')

   # Extension filter - note `f.ext`.
   f.ext.Country().apply('pe')

Django Filters
--------------
Adds filters for Django-specific features.  To install this extension::

   pip install filters[django]

:py:class:`filters.ext.Model`
   Attempts to find a database record that matches the incoming value.

   The filter initializer accepts a few arguments:

   - ``model`` (required) The Django model that will be queried.
   - ``field`` (optional) The name of the field that will be matched against.
      If not provided, the default is ``pk``.

   You may also provide "predicates" to the initializer that will allow you to
   further filter/customize the query as desired.

   Here's an example:

   .. code:: python

      filter_ = f.ext.Model(
        # Find a Post record with a ``slug`` that matches the input.
        model = Post,
        field = 'slug',

        # Predicates
        filter={'published': True},
        exclude={'comments__isnull': True'},
        select_related=('author', 'comments'),
      )

      post = filter_.apply('introducing-filters-library')

   Any method in ``QueryString`` can be used as a predicate so long as that
   method returns a ``QueryString`` object (e.g., ``filter`` and
   ``select_related`` are valid predicates, but ``count`` and ``update`` are
   not).

ISO Filters
-----------
Adds filters for interpreting standard codes and identifiers.  To install this
extension::

   pip install filters[iso]

:py:class:`filters.ext.Country`
   Interprets the incoming value as an
   `ISO 3166-1 alpha-2 or alpha-3 <https://en.wikipedia.org/wiki/ISO_3166-1>`_
   country code.

   The resulting value is a :py:class:`iso3166.Country` object (provided by the
   `iso3166 <https://pypi.python.org/pypi/iso3166>`_ library).

:py:class:`filters.ext.Currency`
   Interprets the incoming value as an
   `ISO 4217 <https://en.wikipedia.org/wiki/ISO_4217>`_ currency code.

   The resulting value is a :py:class:`moneyed.Currency` object (provided by
   the `py-moneyed <https://pypi.python.org/pypi/py-moneyed>`_ library).

:py:class:`filters.ext.Locale`
   Interprets the incoming value as an
   `IETF Language Tag <https://en.wikipedia.org/wiki/IETF_language_tag>`_
   (also known as BCP 47).

   The resulting value is a :py:class:`language_tags.Tag.Tag` object (provided
   by the `language_tags <https://pypi.python.org/pypi/language-tags>`_
   library).
