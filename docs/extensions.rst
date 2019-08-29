Extending the Filters Namespace
===============================
Once you've :doc:`written your own filters </writing_filters>`, you can start
using them right away!

.. code:: python

   In [1]: from filters_iso import Currency

   In [2]: Currency().apply('pen')
   Out[2]: PEN

   In [3]: Currency().apply('foo')
   FilterError: This is not a valid ISO 4217 currency code.

Depending on your situation (and preferences), you might not mind importing
your custom filters explicitly.

However, sometimes all those imports start to get unwieldy, especially if you
have to use namespaces in order to keep them all straight:

.. code:: python

   import filters as f
   import filters_iso as iso_filters
   import api.filters as api_filters

   request_filter =\
     f.FilterMapper({
       'locale': f.Unicode | f.Strip | iso_filters.Locale,
       'username': f.Unicode | f.Strip | api_filters.User | f.Required,
     })

And so on.

Some developers don't mind this; others can't stand it.

For those of you who fall into the latter group, the Filters library provides an
extensions framework that allows you to add your filters to the (nearly)
top-level ``filters.ext`` namespace:

.. code:: python

   import filters as f

   request_filter =\
     f.FilterMapper({
       'locale': f.Unicode | f.Strip | f.ext.Locale,
       'username': f.Unicode | f.Strip | f.ext.User | f.Required,
     })

Note in the above example that the ``Locale`` and ``User`` filters do not need
to be imported explicitly, and they are added automatically to the ``f.ext``
namespace.

Trade-Offs
==========
There is one downside to using the Extensions framework: IDE autocompletion
won't work.

Extension filters are registered at runtime, so your IDE's static analysis has
no way to know what's available in ``filters.ext``.

Depending on your IDE, however, there may be ways to work around this.  For
example, `PyCharm's debugger can be configured to collect type information at
runtime <https://blog.jetbrains.com/pycharm/2013/02/dynamic-runtime-type-inference-in-pycharm-2-7/>`_.

Prerequisites
=============
In order to register your filters with the Extensions framework, your project
must use `setuptools <https://setuptools.readthedocs.io/en/latest/>`_ and have
a valid ``setup.py`` file.

Registering Your Filters
========================
To add custom filters to the ``filters.ext`` namespace, register them as entry
points using the ``filters.extensions`` key.

Here's an example:

.. code:: python

   from setuptools import setup

   setup(
     ...
     entry_points = {
       'filters.extensions': [
         'Country = filters_iso:Country',
         'Currency = filters_iso:Currency',
         'Locale = filters_iso:Locale',
       ],
     },
   )

Note in the example above that you can register as many filters as you want.

.. tip::
   The name that you assign to each entry point is used as the attribute name
   when the corresponding filter is registered.

   To use an absurd example, if you register a filter like this:

   .. code:: python

      setup(
        ...
        entry_points = {
          'filters.extensions': [
            'HelloWorld = filters_iso:Currency',
          ],
        },
      )

   Then it will be registered like this:

   .. code:: python

      In [1]: import filters as f

      In [1]: f.ext.HelloWorld().apply('NZD')
      Out[1]: NZD

   This feature may be useful to resolve conflicts, in the event that two
   filter classes have the same name (see below).

Conflicts
---------
In the event that two filters are registered with the same name, one of them
will replace the other.  The order that entry points are processed is not
defined, so it is not predictable which filter will "win".

Future versions of the Filters library may provide more elegant ways to resolve
these conflicts.

Troubleshooting
---------------
Remember to ``pip install -e .`` each time you modify your entry points; this is
required in order to install the new entry points into your project's
``egg-info`` directory.

If your filter is still not showing up in ``f.ext``, try turning on debug
logging.  You will see log messages as the Filters library searches for
extension filters to load:

.. code:: python

   In [1]: import logging, sys

   In [2]: logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)

   In [3]: import filters as f

   In [4]: dir(f.ext)
   DEBUG:filters.extensions:Registering extension filter filters_iso.Country as Country.
   DEBUG:filters.extensions:Registering extension filter filters_iso.Currency as Currency.
   DEBUG:filters.extensions:Registering extension filter filters_iso.Locale as Locale.
   Out[4]: ['Country', 'Currency', 'Locale']
