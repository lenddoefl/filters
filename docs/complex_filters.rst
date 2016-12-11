===============
Complex Filters
===============
Two common use cases for filters are:

- Process a sequence (e.g., ``list``) of values, applying the same set of
  filters to each value.
- Process a mapping (e.g., ``dict``) of values, applying a different set of
  filters to each value, depending on the key.

The Filters library provides two "complex filters" designed to address these
use cases.

----------------------
Working with Sequences
----------------------
When you need to apply the same set of filters to a sequence of values, use
:py:class:`filters.FilterRepeater`.

``FilterRepeater`` accepts a filter chain, and when applied to an iterable
value, it applies that filter chain to every value in the iterable.

Here's a simple example that ensures that every value in an incoming list is
converted to an int:

.. code-block:: python

   import filters as f

   data = ['42', 86.0, 99]

   input = f.FilterRunner(
     f.FilterRepeater(f.Int | f.Required),
     data,
   )

   assert input.is_valid() is True
   assert input.cleaned_data == [42, 86, 99]

If there are any invalid values in the incoming iterable, ``FilterRepeater``
will capture all filter errors:

.. code-block:: python

   from pprint import pprint
   import filters as f

   data = ['42', 98.6, 'not even close', 99, {12, 34}, None]

   input = f.FilterRunner(
     f.FilterRepeater(f.Int | f.Required),
     data,
   )

   assert input.is_valid() is False
   pprint(input.errors)

The output of the above code is::

   {'1': [{'code': 'not_int', 'message': 'Integer value expected.'}],
    '2': [{'code': 'not_numeric', 'message': 'Numeric value expected.'}],
    '4': [{'code': 'wrong_type',
      'message': 'set is not valid (allowed types: Decimal, float, int, list, str, tuple).'}],
    '5': [{'code': 'empty', 'message': 'This value is required.'}]}

Note that each key in ``input.errors`` corresponds to the index of the invalid
value that it describes.

Using FilterRepeater on Mappings
--------------------------------
You can also use ``FilterRepeater`` on a mapping (e.g., ``dict``).  It will
apply the same filters to every value in the mapping, ensuring that keys are
preserved:

.. code-block:: python

   import filters as f

   data = {
     'alpha':   '42',
     'bravo':   86.0,
     'charlie': 99,
   }

   input = f.FilterRunner(
     f.FilterRepeater(f.Int | f.Required),
     data,
   )

   assert input.is_valid() is True
   assert input.cleaned_data == {
     'alpha':   42,
     'bravo':   86,
     'charlie': 99,
   }

Note what happens if the incoming mapping contains invalid values:

.. code-block:: python

   from pprint import pprint
   import filters as f

   data = {
     'alpha':   '42',
     'bravo':   98.6,
     'charlie': 'not even close',
     'delta':   99,
     'echo':    {12, 34},
     'foxtrot': None,
   }

   input = f.FilterRunner(
     f.FilterRepeater(f.Int | f.Required),
     data,
   )

   assert input.is_valid() is False
   pprint(input.errors)

The output of the above code is::

   {'bravo': [{'code': 'not_int', 'message': 'Integer value expected.'}],
    'charlie': [{'code': 'not_numeric', 'message': 'Numeric value expected.'}],
    'echo': [{'code': 'wrong_type',
              'message': 'set is not valid (allowed types: Decimal, float, int, '
                         'list, str, tuple).'}],
    'foxtrot': [{'code': 'empty', 'message': 'This value is required.'}]}

---------------------
Working with Mappings
---------------------
Often when working with mappings (e.g., ``dict``), you want to apply a different
filter chain to each value, depending on the corresponding key.
:py:class:`FilterMapper` was designed for exactly this situation.

``FilterMapper`` accepts a mapping of filter chains.  When processing an
incoming value, it will "map" its filter chains accordingly.

Here's a simple example:

.. code-block:: python

   import filters as f

   data = {
     'id':      '42',
     'subject': 'Hello, world!',
   }

   mapper = f.FilterMapper({
     'id':      f.Int,
     'subject': f.Unicode | f.NotEmpty | f.MaxLength(16),
   })

   input = f.FilterRunner(mapper, data)

   assert input.is_valid() is True
   assert input.cleaned_data == {
     'id':      42,
     'subject': 'Hello, world!',
   }

When one or more values are invalid, ``FilterMapper`` collects all of the
filter errors, just like ``FilterRepeater``:

.. code-block:: python

   from pprint import pprint
   import filters as f

   data = {
     'id':      [3, 14],
     'subject': 'Did you know that Albert Einstein was born on Pi Day?',
   }

   mapper = f.FilterMapper({
     'id':      f.Int,
     'subject': f.Unicode | f.NotEmpty | f.MaxLength(16),
   })

   input = f.FilterRunner(mapper, data)

   assert input.is_valid() is False
   pprint(input.errors)

The output of the above code is::

   {'id': [{'code': 'not_numeric', 'message': 'Numeric value expected.'}],
    'subject': [{'code': 'too_long',
                 'message': 'Value is too long (length must be < 16).'}]}


Validating Keys
---------------
By default, ``FilterMapper`` is very lenient about what keys the incoming value
can contain:

.. code-block:: python

   import filters as f

   data = {
     'id':          -1,
     'attachment':  'virus.exe',
   }

   mapper = f.FilterMapper({
     'id':      f.Int,
     'subject': f.Unicode | f.NotEmpty | f.MaxLength(16),
   })

   input = f.FilterRunner(mapper, data)

   assert input.is_valid() is True
   assert input.cleaned_data == {
     'id':          -1,
     'subject':     None,
     'attachment':  'virus.exe',
   }

Note that the incoming value was missing the ``subject`` key, and it contained
the extra key ``attachment``, but the FilterMapper ignored these issues.

If you want ``FilterMapper`` to check that the incoming value has the correct
keys, there are two additional parameters you can set in the filter initializer:
``allow_extra_keys`` and ``allow_missing_keys``.

.. code-block:: python

   from pprint import pprint
   import filters as f

   data = {
     'id':          -1,
     'attachment':  'virus.exe',
   }

   mapper = f.FilterMapper(
     {
       'id':      f.Int,
       'subject': f.Unicode | f.NotEmpty | f.MaxLength(16),
     },

     # Only allow keys that we are expecting.
     allow_extra_keys = False,

     # All keys are required.
     allow_missing_keys = False,
   )

   input = f.FilterRunner(mapper, data)

   assert input.is_valid() is False
   pprint(input.errors)

The output of the above code is::

   {'attachment': [{'code': 'unexpected',
                    'message': 'Unexpected key "attachment".'}],
    'subject': [{'code': 'missing', 'message': 'subject is required.'}]}

You can also provide explicit key names for these parameters:

.. code-block:: python

   from pprint import pprint
   import filters as f

   data = {
     'from':        'admin@facebook.com',
     'attachment':  'virus.exe',
   }

   mapper = f.FilterMapper(
     {
       'id':      f.Int,
       'subject': f.Unicode | f.NotEmpty | f.MaxLength(16),
     },

     # Ignore `attachment` if present,
     # but other extra keys are invalid.
     allow_extra_keys = {'attachment'},

     # Only `subject` is optional.
     allow_missing_keys = {'subject'},
   )

   input = f.FilterRunner(mapper, data)

   assert input.is_valid() is False
   pprint(input.errors)

The output of the above code is::

   {'from': [{'code': 'unexpected', 'message': 'Unexpected key "from".'}],
    'id': [{'code': 'missing', 'message': 'id is required.'}]}

Note that the ``FilterMapper`` ignored the extra ``attachment`` and missing
``subject``, but the extra ``from`` and missing ``id`` were still treated as
invalid.

-------------
Filterception
-------------
Both ``FilterRepeater`` and ``FilterMapper`` can be included in a filter chain,
just like any other filter.

Here's a simple example that validates a collection of addresses:

.. code-block:: python

   import filters as f

   data = [
     {
       'street':  ['Malecon de la Reserva 610'],
       'city':    'Lima',
       'country': 'Peru',
     },

     {
       'street':  ['Parc du Champs de Mars', '5 Avenue Anatole France'],
       'city':    'Paris',
       'country': 'France',
     },
   ]

   repeater = f.FilterRepeater(
     f.FilterMapper({
       'street':  f.FilterRepeater(f.Unicode),
       'city':    f.Unicode,
       'country': f.Unicode,
     })
   )

   input = f.FilterRunner(repeater, data)

   assert input.is_valid() is True
   assert input.cleaned_data == data
