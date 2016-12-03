=======
Filters
=======

The Filters library provides an easy and readable way to create complex
data validation and processing pipelines.

Here's an example of using Filters to validate and process some JSON::

    import datetime
    import decimal
    import filters as f

    data = u'{"birthday": "2006-11-23", "gender": "M", "utcOffset": "-5"}'

    filter_ = f.FilterRunner(
        f.JsonDecode
      | f.FilterMapper(
          {
            'birthday': f.Date,
            'gender':   f.CaseFold | f.Choice(choices={'m', 'f', 'x'}),

            # :see: https://en.wikipedia.org/wiki/List_of_UTC_time_offsets
            'utcOffset':
                f.Decimal
              | f.Min(decimal.Decimal('-15'))
              | f.Max(decimal.Decimal('+15'))
              | f.Round(to_nearest='0.25'),
          },
          allow_extra_keys   = False,
          allow_missing_keys = True,
        ),

      data,
    )

    if filter_.is_valid():
      cleaned_data = filter_.cleaned_data

      assert cleaned_data == {
        'birthday':   datetime.date(2006, 11, 23),
        'gender':     'm',
        'utcOffset':  decimal.Decimal('-5.0'),
      }
    else:
      for key, errors in filter_.errors.items():
        print('{key}:'.format(key=key))
        for error in errors:
          print('  - ({error[code]}) {error[message]}'.format(error=error))

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
