.. image:: https://travis-ci.org/eflglobal/filters.svg?branch=master
   :target: https://travis-ci.org/eflglobal/filters
.. image:: https://readthedocs.org/projects/filters/badge/?version=latest
   :target: http://filters.readthedocs.io/

=======
Filters
=======
The Filters library provides an easy and readable way to create complex
data validation and processing pipelines, including:

- Validating complex JSON structures in API requests or config files.
- Parsing timestamps and converting to UTC.
- Converting Unicode strings to NFC, normalizing line endings and removing
  unprintable characters.
- Decoding Base64, including URL-safe variants.

And much more!

The output from one filter can be "piped" into the input of another, enabling
you to "chain" filters together to quickly and easily create complex data
pipelines.

Examples
========

Validate a latitude position and round to manageable precision:

.. code:: python

   (
       f.Required
     | f.Decimal
     | f.Min(Decimal(-90))
     | f.Max(Decimal(90))
     | f.Round(to_nearest='0.000001')
   ).apply('-12.0431842')

Parse an incoming value as a datetime, convert to UTC and strip tzinfo:

.. code:: python

   f.Datetime(naive=True).apply('2015-04-08T15:11:22-05:00')

Convert every value in an iterable (e.g., list) to unicode and strip
leading/trailing whitespace.
This also applies `Unicode normalization`_, strips unprintable characters and
normalizes line endings automatically.

.. code:: python

   f.FilterRepeater(f.Unicode | f.Strip).apply([
     b'\xe2\x99\xaa ',
     b'\xe2\x94\x8f(\xc2\xb0.\xc2\xb0)\xe2\x94\x9b ',
     b'\xe2\x94\x97(\xc2\xb0.\xc2\xb0)\xe2\x94\x93 ',
     b'\xe2\x99\xaa ',
   ])

Parse a JSON string and check that it has correct structure:

.. code:: python

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
   ).apply('{"birthday":"1879-03-14", "gender":"M", "utcOffset":"1"}')

============
Requirements
============
Filters is compatible with Python versions 3.6, 3.5 and 2.7.

============
Installation
============
Install the latest stable version via pip::

    pip install filters

Install the latest development version::

    pip install https://github.com/eflglobal/filters/archive/develop.zip


.. _Unicode normalization: https://en.wikipedia.org/wiki/Unicode_equivalence
