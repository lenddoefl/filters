.. image:: https://travis-ci.org/todofixthis/filters.svg?branch=master
   :target: https://travis-ci.org/todofixthis/filters
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
--------
Validate a latitude position and round to manageable precision:

.. code-block:: python

   (
       f.Required |
       f.Decimal |
       f.Min(Decimal(-90)) |
       f.Max(Decimal(90)) |
       f.Round(to_nearest='0.000001')
   ).apply('-12.0431842')

Parse an incoming value as a datetime, convert to UTC and strip tzinfo:

.. code-block:: python

   f.Datetime(naive=True).apply('2015-04-08T15:11:22-05:00')

Convert every value in an iterable (e.g., list) to unicode and strip
leading/trailing whitespace.
This also applies `Unicode normalization`_, strips unprintable characters and
normalizes line endings automatically.

.. code-block:: python

   f.FilterRepeater(f.Unicode | f.Strip).apply([
       b'\xe2\x99\xaa ',
       b'\xe2\x94\x8f(\xc2\xb0.\xc2\xb0)\xe2\x94\x9b ',
       b'\xe2\x94\x97(\xc2\xb0.\xc2\xb0)\xe2\x94\x93 ',
       b'\xe2\x99\xaa ',
   ])

Parse a JSON string and check that it has correct structure:

.. code-block:: python

   (
       f.JsonDecode |
       f.FilterMapper(
           {
               'birthday':  f.Date,
               'gender':    f.CaseFold | f.Choice(choices={'m', 'f', 'x'}),

               'utcOffset':
                   f.Decimal |
                   f.Min(Decimal('-15')) |
                   f.Max(Decimal('+15')) |
                   f.Round(to_nearest='0.25'),
           },

           allow_extra_keys   = False,
           allow_missing_keys = False,
       )
   ).apply('{"birthday":"1879-03-14", "gender":"M", "utcOffset":"1"}')


Requirements
------------
Filters is compatible with the following Python versions:

- 3.8
- 3.7
- 3.6
- 3.5

.. note::
  Filters is **not** compatible with Python 2.


Installation
------------
Install the latest stable version via pip::

    pip install phx-filters


Extensions
~~~~~~~~~~
The following extensions are available:

- `Django Filters`_: Adds filters designed to work with Django applications.
  To install::

      pip install phx-filters[django]

- `ISO Filters`_: Adds filters for interpreting standard codes and identifiers.
  To install::

      pip install phx-filters[iso]

.. tip::
   To install multiple extensions, separate them with commas, e.g.::

      pip install phx-filters[django,iso]


Running Unit Tests
------------------
To run unit tests after installing from source::

  python setup.py test

This project is also compatible with `tox`_, which will run the unit tests in
different virtual environments (one for each supported version of Python).

Install the package with the ``test-runner`` extra to set up the necessary
dependencies, and then you can run the tests with the ``tox`` command::

  pip install -e .[test-runner]
  tox -p all


Documentation
-------------
Documentation is available on `ReadTheDocs`_.

If you are installing from source (see above), you can also build the
documentation locally:

#. Install extra dependencies (you only have to do this once)::

      pip install '.[docs-builder]'

#. Switch to the ``docs`` directory::

      cd docs

#. Build the documentation::

      make html


.. _Django Filters: https://pypi.python.org/pypi/filters-django
.. _ISO Filters: https://pypi.python.org/pypi/filters-iso
.. _ReadTheDocs: https://filters.readthedocs.io/
.. _tox: https://tox.readthedocs.io/
.. _Unicode normalization: https://en.wikipedia.org/wiki/Unicode_equivalence
