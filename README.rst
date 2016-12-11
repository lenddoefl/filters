=======
Filters
=======
The Filters library provides an easy and readable way to create complex
data validation and processing pipelines, including:

- Validating complex JSON structures in API requests or config files.
- Parsing timestamps and converting to UTC.
- Converting Unicode strings to NFC, normalizing line endings and removing
  unprintable characters.

And much more!

Here are a few simple examples:

.. code:: python

   # Validate a latitude position and round to manageable precision.
   (
       f.Required
     | f.Decimal
     | f.Min(Decimal(-90))
     | f.Max(Decimal(90)
     | f.Round(to_nearest='0.000001')
   ).apply(int_or_string_value)

   # Convert an incoming value into a naive datetime.
   f.Datetime(naive=True).apply(string_or_datetime_value)

   # Convert every value in an iterable (e.g., list) to unicode.
   # This also applies Unicode normalization, strips unprintable
   #  characters and normalizes line endings automatically.
   f.FilterRepeater(f.Unicode).apply(iterable_value)

   # Parse a JSON string and check that it has correct structure.
   (
       f.JsonDecode
     | f.FilterMapper(
         {
           'birthday':  f.Date,
           'gender':    f.CaseFold | f.Choice(choices={'m', 'f', 'x'}),

           'utcOffset':
               f.Decimal
             | f.Min(Decimal('-15'))
             | f.Max(Decimal('+15'))
             | f.Round(to_nearest='0.25'),
         },

         allow_extra_keys   = False,
         allow_missing_keys = False,
       )
   ).apply(json_string)

Notice in the above examples that output from one filter can be "piped" into
the input of another.  This allows you to "chain" filters together to quickly
and easily create complex data pipelines.

============
Requirements
============
Filters is compatible with Python 2.7 and 3.5.

============
Installation
============
Install the latest stable version via pip::

    pip install filters

Install the latest development version::

    pip install https://github.com/eflglobal/filters/archive/develop.zip

