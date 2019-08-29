Getting Started
===============
The fastest way to get started with filters is to use the ``FilterRunner``
class.  This class provides an interface very similar to a Django form.

.. code-block:: python

   import datetime
   import filters as f

   # Incoming data.
   data = u'1879-03-14'

   # Initialize the FilterRunner.
   input = f.FilterRunner(f.Date, data)

   if input.is_valid():
     # Input is valid; do something with the filtered data.
     cleaned_data = input.cleaned_data
     assert cleaned_data == datetime.date(1879, 3, 14)

   else:
     # Input is not valid; display error message(s).
     for key, errors in input.errors.items():
       print('{key}:'.format(key=key))
       for error in errors:
         print('  - ({error[code]}) {error[message]}'.format(error=error))

``FilterRunner`` provides a few key attributes to make it easy to apply filters:

- ``is_valid()``:  Returns whether the value is valid.
- ``cleaned_data``:  If the value is valid, this property holds the filtered
  value(s).
- ``errors``:  If the value is not valid, this property holds the validation
  errors.

Chaining Filters
================
The filters library conforms to the unix philosophy of,
`"Do One Thing, and Do It Well" <https://en.wikipedia.org/wiki/Unix_philosophy#Do_One_Thing_and_Do_It_Well>`_.

Each filter provides a specific transformation and/or validation feature.  This
alone can be useful, but the real power of the filters library lies in its
ability to "chain" filters together.

By using the ``|`` operator, you can "pipe" the output of one filter directly
into the input of another.  This allows you to quickly and easily create complex
data pipelines.

Here's an example:

.. code-block:: python

   import filters as f

   data = 'Остерегайтесь Дуга'

   input = f.FilterRunner(
     # Convert to unicode, reject empty string, fold case
     # and split into words.
     f.Unicode | f.NotEmpty | f.CaseFold | f.Split(r'\W+'),
     data,
   )

   assert input.is_valid()
   print(input.cleaned_data) # ['остерегайтесь', 'дуга']

Much Ado About None
===================
``None`` is a special value to the Filters library.  By default, it passes
every filter, no matter how strictly configured.

For example:

.. code-block:: python

   data = None

   input = f.FilterRunner(
     # Convert to unicode, reject empty string, fold case
     # and split into words.
     f.Unicode | f.NotEmpty | f.CaseFold | f.Split(r'\W+'),
     data,
   )

   input.is_valid() # Returns True!

If you want to reject ``None``, add the ``Required`` filter to your chain:

.. code-block:: python

   data = None

   input = f.FilterRunner(
     # Note that we replace NotEmpty with Required.
     f.Unicode | f.Required | f.CaseFold | f.Split(r'\W+'),
     data,
   )

   input.is_valid() # False

List of Filters
===============
See :doc:`/filters_list` for a list of the filters that come bundled with the
Filters library.

You can also :doc:`write your own filters </writing_filters>`.

Sequences and Mappings
======================
The Filters library also provides two "complex filters" that you can use to
apply filters to the contents of sequences (e.g., ``list``) and mappings (e.g.,
``dict``).

These are covered in a separate section: :doc:`/complex_filters`.
