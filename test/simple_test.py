# coding=utf-8
from __future__ import absolute_import, division, print_function, \
    unicode_literals

from datetime import datetime, date
from decimal import Decimal
from xml.etree.ElementTree import Element

from dateutil.tz import tzoffset
from pytz import utc
from six import PY2, binary_type, python_2_unicode_compatible, text_type

import filters as f
from filters.test import BaseFilterTestCase


class Lengthy(object):
    """
    A class that defines `__len__`, used to test Filters that check for
        object length.
    """
    def __init__(self, length):
        super(Lengthy, self).__init__()
        self.length = length

    def __len__(self):
        return self.length


# noinspection SpellCheckingInspection
class Bytesy(object):
    """
    A class that defines `__bytes__`, used to test Filters that convert
        values into byte strings.
    """
    def __init__(self, value):
        super(Bytesy, self).__init__()
        self.value = value

    def __bytes__(self):
        return binary_type(self.value)

    if PY2:
        __str__ = __bytes__


# noinspection SpellCheckingInspection
@python_2_unicode_compatible
class Unicody(object):
    """
    A class that defines `__str__`, used to test Filters that convert
        values into unicodes.
    """
    def __init__(self, value):
        super(Unicody, self).__init__()
        self.value = value

    def __str__(self):
        return text_type(self.value)


class ByteArrayTestCase(BaseFilterTestCase):
    filter_type = f.ByteArray

    def test_pass_none(self):
        """
        `None` always passes this Filter.

        Use `Required | ByteArray` if you want to reject `None`.
        """
        self.assertFilterPasses(None)

    def test_pass_bytes(self):
        """The incoming value is a byte string."""
        self.assertFilterPasses(
            b'|\xa8\xc1.8\xbd4\xd5s\x1e\xa6%+\xea!6',

            # Note that "numeric" characters like "8" and "6" are NOT
            #   interpreted literally.
            # This matches the behavior of Python's built-in bytearray
            #   class.
            bytearray([
                124, 168, 193, 46, 56, 189, 52, 213,
                115, 30, 166, 37, 43, 234, 33, 54,
            ]),
        )

    def test_pass_string(self):
        """
        The incoming value is a string.

        This is generally not a recommended use for ByteArray, but
            sometimes it's unavoidable.
        """
        self.assertFilterPasses(
            u'\xccK\xdf\xb1\x8bM\xc7\x01\xf0B\xac":\xeb>\x85',
            bytearray([
                195, 140, 75, 195, 159, 194, 177, 194, 139, 77, 195, 135,
                1, 195, 176, 66, 194, 172, 34, 58, 195, 171, 62, 194, 133,
            ]),
        )

    def test_pass_string_alternate_encoding(self):
        """
        If you want to filter unicodes, you can specify the encoding to
            use.
        """
        self.assertFilterPasses(
            self._filter(
                u'\xccK\xdf\xb1\x8bM\xc7\x01\xf0B\xac":\xeb>\x85',
                encoding='latin-1',
            ),
            bytearray([
                204, 75, 223, 177, 139, 77, 199, 1,
                240, 66, 172, 34, 58, 235, 62, 133,
            ]),
        )

    def test_pass_bytearray(self):
        """The incoming value is already a bytearray."""
        self.assertFilterPasses(
            bytearray([
                84, 234, 48, 177, 119, 69, 36, 147,
                214, 13, 54, 12, 56, 168, 107, 2,
            ])
        )

    def test_pass_iterable(self):
        """
        The incoming value is an iterable containing integers between
            0 and 255, inclusive.
        """
        self.assertFilterPasses(
            [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233],
            bytearray([0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233])
        )

    def test_fail_iterable_wrong_types(self):
        """
        The incoming value is an iterable, but the values are not
            integers.
        """
        self.assertFilterErrors(
            # The first 2 values are valid.  None of the others
            #   are.
            # It's arguable whether booleans should be valid, but
            #   they are technically ints, and Python's bytearray
            #   allows them, so the Filter does, too.
            [1, True, '1', b'1', 1.1, bytearray([1])],

            {
                #
                # String values inside of an iterable are not
                #   considered valid.
                #
                # It's true that we do have a precedent for how to
                #   treat string values (convert each character to
                #   its ordinal value), but that only works for
                #   strings that can fit into a single byte.
                #
                # How would we convert `['11', 'foo']` into a
                #   bytearray?
                #
                # To keep things as consistent as possible, the
                #   Filter will treat strings inside of iterables
                #   the same way it treats anything else that isn't
                #   an int.
                #
                '2': [f.Type.CODE_WRONG_TYPE],
                '3': [f.Type.CODE_WRONG_TYPE],

                # Floats are not allowed in bytearrays.  How would
                #   that even work?
                '4': [f.Type.CODE_WRONG_TYPE],

                # Anything else that isn't an int is invalid, even
                #   if it contains ints.
                # After all, you can't squeeze multiple bytes into
                #   a single byte!
                '5': [f.Type.CODE_WRONG_TYPE],
            },
        )

    def test_fail_iterable_out_of_bounds(self):
        """
        The incoming value is an iterable with integers, but it
            contains values outside the acceptable range.

        Each value inside a bytearray must fit within 1 byte, so its
            value must satisfy `0 <= x < 2^8`.
        """
        self.assertFilterErrors(
            [-1, 0, 1, 255, 256, 9001],

            {
                '0': [f.Min.CODE_TOO_SMALL],
                '4': [f.Max.CODE_TOO_BIG],
                '5': [f.Max.CODE_TOO_BIG],
            },
        )

    def test_fail_unencodable_unicode(self):
        """
        The incoming value is a unicode that cannot be encoded using
            the specified encoding.
        """
        value = '\u043b\u0435\u0431\u044b\u0440'

        # The default encoding (utf-8) can handle this just fine.
        self.assertFilterPasses(
            value,
            bytearray([208, 187, 208, 181, 208, 177, 209, 139, 209, 128]),
        )

        # However, if we switch to a single-byte encoding, we run into
        #   serious problems.
        self.assertFilterErrors(
            self._filter(value, encoding='latin-1'),
            [f.ByteArray.CODE_BAD_ENCODING],
        )


class ByteStringTestCase(BaseFilterTestCase):
    filter_type = f.ByteString

    def test_pass_none(self):
        """
        `None` always passes this Filter.

        Use `Required | ByteString` if you want to reject `None`.
        """
        self.assertFilterPasses(None)

    def test_pass_unicode(self):
        """
        The incoming value is a unicode.
        """
        self.assertFilterPasses(
            'Iñtërnâtiônàlizætiøn',

            # 'Iñtërnâtiônàlizætiøn' encoded as bytes using utf-8:
            b'I\xc3\xb1t\xc3\xabrn\xc3\xa2ti\xc3'
            b'\xb4n\xc3\xa0liz\xc3\xa6ti\xc3\xb8n',
        )

    def test_pass_bytes_utf8(self):
        """
        The incoming value is a byte string, already encoded as UTF-8.
        """
        self.assertFilterPasses(
            b'I\xc3\xb1t\xc3\xabrn\xc3\xa2ti\xc3'
            b'\xb4n\xc3\xa0liz\xc3\xa6ti\xc3\xb8n'
        )

    def test_fail_bytes_non_utf8(self):
        """
        The incoming value is a byte string, but encoded using a
            different codec.
        """
        # 'Iñtërnâtiônàlizætiøn' encoded as bytes using ISO-8859-1:
        incoming = b'I\xf1t\xebrn\xe2ti\xf4n\xe0liz\xe6ti\xf8n'

        self.assertFilterErrors(
            incoming,
            [f.ByteString.CODE_DECODE_ERROR],
        )

        # In order for this to work, we have to tell the Filter what
        #   encoding to use:
        self.assertFilterPasses(
            self._filter(incoming, encoding='iso-8859-1'),

            # The result is re-encoded using UTF-8.
            b'I\xc3\xb1t\xc3\xabrn\xc3\xa2ti\xc3'
            b'\xb4n\xc3\xa0liz\xc3\xa6ti\xc3\xb8n',
        )

    def test_pass_string_like_object(self):
        """
        The incoming value is an object that can be cast as a unicode.
        """
        self.assertFilterPasses(
            Unicody('༼ つ ◕_◕ ༽つ'),

            # Stoned Kirby?  Jigglypuff in dance mode?
            # I have no idea what this is.
            b'\xe0\xbc\xbc \xe3\x81\xa4 \xe2\x97\x95_'
            b'\xe2\x97\x95 \xe0\xbc\xbd\xe3\x81\xa4',
        )

    def test_pass_bytes_like_object(self):
        """
        The incoming value is an object that can be cast as a byte
            string.
        """
        value = (
            # Person
            b'(\xe2\x95\xaf\xc2\xb0\xe2\x96\xa1\xc2\xb0)'
            # Particle Effects
            b'\xe2\x95\xaf\xef\xb8\xb5 '
            # Table
            b'\xe2\x94\xbb\xe2\x94\x81\xe2\x94\xbb'
        )

        self.assertFilterPasses(Bytesy(value), value)

    def test_pass_boolean(self):
        """
        The incoming value is a boolean (treated as an int).
        """
        self.assertFilterPasses(True, b'1')

    def test_pass_decimal_with_scientific_notation(self):
        """
        The incoming value is a Decimal that was parsed from scientific
            notation.
        """
        # Note that `str(Decimal('2.8E6')` yields b'2.8E+6', which is
        #   not what we want!
        self.assertFilterPasses(
            Decimal('2.8E6'),
            b'2800000',
        )

    def test_pass_xml_element(self):
        """The incoming value is an ElementTree XML Element."""
        self.assertFilterPasses(
            Element('foobar'),
            b'<foobar />',
        )

    def test_unicode_normalization_off_by_default(self):
        """
        By default, the Filter does not apply normalization before
            encoding.

        :see: https://en.wikipedia.org/wiki/Unicode_equivalence
        :see: http://stackoverflow.com/q/16467479
        """
        self.assertFilterPasses(
            #   U+0065 LATIN SMALL LETTER E
            # + U+0301 COMBINING ACUTE ACCENT
            # (2 code points)
            'Ame\u0301lie',

            # Result is the same string, encoded using UTF-8.
            b'Ame\xcc\x81lie',
        )

    def test_unicode_normalization_forced(self):
        """
        You can force the Filter to apply normalization before encoding.

        :see: https://en.wikipedia.org/wiki/Unicode_equivalence
        :see: http://stackoverflow.com/q/16467479
        """
        self.assertFilterPasses(
            self._filter(
                # Same decomposed sequence from previous test...
                'Ame\u0301lie',

                # ... but this time we tell the Filter to normalize the
                #   value before encoding it.
                normalize = True,
            ),

            # U+00E9 LATIN SMALL LETTER E WITH ACUTE
            # (1 code point, encoded as bytes)
            b'Am\xc3\xa9lie',
        )

    def test_remove_non_printables_off_by_default(self):
        """
        By default, the Filter does not remove non-printable
            characters.
        """
        self.assertFilterPasses(
            # \u0000-\u001f are ASCII control characters.
            # \uffff is a Unicode control character.
            '\u0010Hell\u0000o,\u001f wor\uffffld!',

            b'\x10Hell\x00o,\x1f wor\xef\xbf\xbfld!',
        )

    def test_remove_non_printables_forced(self):
        """
        You can force the Filter to remove non-printable characters
            before encoding.
        """
        self.assertFilterPasses(
            self._filter(
                '\u0010Hell\u0000o,\u001f wor\uffffld!',
                normalize = True,
            ),
            b'Hello, world!',
        )

    def test_newline_normalization_off_by_default(self):
        """
        By default, the Filter does not normalize line endings.
        """
        self.assertFilterPasses(
            'unix\n - windows\r\n - weird\r\r\n',
            b'unix\n - windows\r\n - weird\r\r\n',
        )

    def test_newline_normalization_forced(self):
        """
        You can force the Filter to normalize line endings.
        """
        self.assertFilterPasses(
            self._filter('unix\n - windows\r\n - weird\r\r\n', normalize=True),
            b'unix\n - windows\n - weird\n\n',
        )


class ChoiceTestCase(BaseFilterTestCase):
    filter_type = f.Choice

    def test_pass_none(self):
        """
        `None` always passes this Filter.

        Use `Required | Choice` if you want to reject `None`.
        """
        self.assertFilterPasses(
            # Even if you specify no valid choices, `None` still
            #   passes.
            self._filter(None, choices=()),
        )

    def test_pass_valid_value(self):
        """The incoming value matches one of the choices."""
        self.assertFilterPasses(
            self._filter('Curly', choices=('Moe', 'Larry', 'Curly')),
        )

    def test_fail_invalid_value(self):
        """The incoming value does not match any of the choices."""
        self.assertFilterErrors(
            self._filter('Shemp', choices=('Moe', 'Larry', 'Curly')),
            [f.Choice.CODE_INVALID],
        )


class DateTestCase(BaseFilterTestCase):
    filter_type = f.Date

    def test_pass_none(self):
        """
        `None` always passes this Filter.

        Use `Required | Date` if you want to reject `None`.
        """
        self.assertFilterPasses(None)

    def test_pass_naive_timestamp(self):
        """
        The incoming value is a naive timestamp (no timezone info).
        """
        self.assertFilterPasses(
            '2015-05-11 14:56:58',
            date(2015, 5, 11),
        )

    def test_pass_aware_timestamp(self):
        """The incoming value includes timezone info."""
        self.assertFilterPasses(
            # Note that the value we are parsing is 5 hours behind UTC.
            '2015-05-11T19:56:58-05:00',

            # The resulting date appears to occur 1 day later because
            #   that's the date according to UTC.
            date(2015, 5, 12)
        )

    def test_pass_naive_timestamp_default_timezone(self):
        """
        The incoming value is a naive timestamp, but the Filter is
            configured not to treat naive timestamps as UTC.
        """
        self.assertFilterPasses(
            self._filter(
                '2015-05-12 03:20:03',

                # The Filter is configured to parse naive timestamps as
                #   if they are UTC+8.
                timezone = tzoffset('UTC+8', 8*3600)
            ),

            # The resulting date appears to occur 1 day earlier because
            #   the Filter subtracted 8 hours to convert the value to
            #   UTC.
            date(2015, 5, 11),
        )

    def test_pass_aware_timestamp_default_timezone(self):
        """
        The Filter's default timezone has no effect if the incoming
            value already contains timezone info.
        """
        self.assertFilterPasses(
            # The incoming timestamp is from UTC+4, but the Filter is
            #   configured to use UTC-11 by default.
            self._filter(
                '2015-05-11T03:14:38+04:00',
                timezone = tzoffset('UTC-11', -11*3600)
            ),

            # Because the incoming timestamp has timezone info, the
            #   Filter uses that instead of the default value.
            # Note that the this test will fail if the Filter uses the
            #   UTC-11 timezone (the result will be 1 day ahead).
            date(2015, 5, 10),
        )

    def test_pass_alternate_timezone_syntax(self):
        """
        When setting the default timezone for the Filter, you can use
            an int/float offset (number of hours from UTC) instead of a
            tzoffset object.
        """
        self.assertFilterPasses(
            # Note that we use an int value instead of constructing a
            #   tzoffset for `timezone`.
            self._filter('2015-05-11 21:14:38', timezone=-8),
            date(2015, 5, 12),
        )

    def test_pass_datetime_utc(self):
        """
        The incoming value is a datetime object that is already set to
            UTC.
        """
        self.assertFilterPasses(
            datetime(2015, 6, 27, 10, 5, 48, tzinfo=utc),
            date(2015, 6, 27),
        )

    def test_pass_datetime_non_utc(self):
        """
        The incoming value is a datetime object with a non-UTC
            timezone.
        """
        self.assertFilterPasses(
            datetime(
                2015, 6, 27, 22, 6, 32,
                tzinfo=tzoffset('UTC-5', -5*3600),
            ),

            # As you probably already guessed, the datetime gets
            #   converted to UTC before it is converted to a date.
            date(2015, 6, 28),
        )

    def test_pass_datetime_naive(self):
        """
        The incoming value is a datetime object without timezone info.
        """
        self.assertFilterPasses(
            # The Filter will assume that this datetime is UTC-3 by
            #   default.
            self._filter(datetime(2015, 6, 27, 23, 7, 18), timezone=-3),

            # The datetime is converted from UTC-3 to UTC before it is
            #   converted to a date.
            date(2015, 6, 28),
        )

    def test_pass_date(self):
        """The incoming value is a date object."""
        self.assertFilterPasses(date(2015, 6, 27))

    def test_fail_invalid_value(self):
        """
        The incoming value cannot be interpreted as a date.

        Insert socially-awkward nerd joke here.
        """
        self.assertFilterErrors(
            'this is not a date',
            [f.Date.CODE_INVALID],
        )


class DatetimeTestCase(BaseFilterTestCase):
    filter_type = f.Datetime

    def test_pass_none(self):
        """
        `None` always passes this Filter.

        Use `Required | Datetime` if you want to reject `None`.
        """
        self.assertFilterPasses(None)

    def test_pass_naive_timestamp(self):
        """
        The incoming value is a naive timestamp (does not include
            timezone info).
        """
        self.assertFilterPasses(
            '2015-05-11 14:56:58',
            datetime(2015, 5, 11, 14, 56, 58, tzinfo=utc),
        )

    def test_pass_aware_timestamp(self):
        """
        The incoming value is a timestamp that includes timezone info.
        """
        self.assertFilterPasses(
            # Note that the value we are parsing is 5 hours behind UTC.
            '2015-05-11T14:56:58-0500',

            datetime(2015, 5, 11, 19, 56, 58, tzinfo=utc)
        )

    def test_pass_naive_timestamp_default_timezone(self):
        """
        The incoming value is a naive timestamp, but the Filter is
            configured not to treat naive timestamps as UTC.
        """
        self.assertFilterPasses(
            # The incoming value is a naive timestamp, and the Filter
            #   is configured to use UTC+8 by default.
            self._filter(
                '2015-05-12 09:20:03',
                timezone = tzoffset('UTC+8', 8*3600),
            ),

            # The resulting datetime is still converted to UTC.
            datetime(2015, 5, 12, 1, 20, 3, tzinfo=utc),
        )

    def test_pass_aware_timestamp_default_timezone(self):
        """
        The Filter's default timezone has no effect if the incoming
            value already contains timezone info.
        """
        self.assertFilterPasses(
            # The incoming value is UTC+4, but the Filter is configured
            #   to use UTC-1 by default.
            self._filter(
                '2015-05-11T21:14:38+04:00',
                timezone = tzoffset('UTC-1', -1*3600)
            ),

            # The incoming values timezone info is used instead of the
            #   default.
            # Note that the resulting datetime is still converted to
            #   UTC.
            datetime(2015, 5, 11, 17, 14, 38, tzinfo=utc),
        )

    def test_pass_alternate_timezone_syntax(self):
        """
        When setting the default timezone for the Filter, you can use
            an int/float offset (number of hours from UTC) instead of a
            tzoffset object.
        """
        self.assertFilterPasses(
            # Note that we use an int value instead of constructing a
            #   tzoffset for `timezone`.
            self._filter('2015-05-11 21:14:38', timezone=3),

            datetime(2015, 5, 11, 18, 14, 38, tzinfo=utc),
        )

    def test_pass_datetime_utc(self):
        """
        The incoming value is a datetime object that is already set to
            UTC.
        """
        self.assertFilterPasses(datetime(2015, 6, 27, 10, 5, 48, tzinfo=utc))

    def test_pass_datetime_non_utc(self):
        """
        The incoming value is a datetime object that is already set to
            a non-UTC timezone.
        """
        self.assertFilterPasses(
            datetime(2015, 6, 27, 10, 6, 32, tzinfo=tzoffset('UTC-5',-5*3600)),
            datetime(2015, 6, 27, 15, 6, 32, tzinfo=utc),
        )

    def test_datetime_naive(self):
        """
        The incoming value is a datetime object that does not have
            timezone info.
        """
        self.assertFilterPasses(
            # The Filter is configured to assume UTC-3 if the incoming
            #   value has no timezone info.
            self._filter(datetime(2015, 6, 27, 18, 7, 18), timezone=-3),

            datetime(2015, 6, 27, 21, 7, 18, tzinfo=utc),
        )

    def test_pass_date(self):
        """The incoming value is a date object."""
        self.assertFilterPasses(
            # The Filter is configured to assume UTC+12 if the incoming
            #   value has no timezone info.
            self._filter(date(2015, 6, 27), timezone=12),

            datetime(2015, 6, 26, 12, 0, 0, tzinfo=utc),
        )

    def test_return_naive_datetime(self):
        """
        You can configure the filter to return a naive datetime object
            (e.g., for storing in a database).

        Note that the datetime is still converted to UTC before its
            tzinfo is removed.
        """
        self.assertFilterPasses(
            self._filter(
                datetime(
                    2015, 7, 1, 9, 22, 10,
                    tzinfo=tzoffset('UTC-5', -5*3600),
                ),

                # Note that we pass `naive=True` to the Filter's
                #   initializer.
                naive = True,
            ),

            # The resulting datetime is converted to UTC before its
            #   timezone info is stripped.
            datetime(2015, 7, 1, 14, 22, 10, tzinfo=None),
        )

    def test_fail_invalid_value(self):
        """
        The incoming value cannot be parsed as a datetime.
        """
        self.assertFilterErrors(
            'this is not a datetime',
            [f.Datetime.CODE_INVALID],
        )


class DecimalTestCase(BaseFilterTestCase):
    filter_type = f.Decimal

    def test_pass_none(self):
        """
        `None` always passes this Filter.

        Use `Required | Decimal` if you want to reject `None`.
        """
        self.assertFilterPasses(None)

    def test_pass_valid_decimal(self):
        """The incoming value can be interpreted as a Decimal."""
        value = '3.1415926'

        self.assertFilterPasses(value, Decimal(value))

    def test_pass_max_precision(self):
        """
        You can limit the max precision of the resulting Decimal
            object.

        Note that a too-precise value is not considered invalid;
            instead, it gets rounded to the expected precision.
        """
        self.assertFilterPasses(
            self._filter('3.1415926', max_precision=3),
            Decimal('3.142'),
        )

    def test_pass_zero(self):
        """
        0 is also considered a valid Decimal value.
        """
        value = '0'
        self.assertFilterPasses(value, Decimal(value))

    def test_pass_scientific_notation(self):
        """
        Scientific notation is considered valid, as in certain cases it
            may be the only way to represent a really large or small
            value.
        """
        value = '2.8E-12'
        self.assertFilterPasses(value, Decimal(value))

    def test_pass_boolean(self):
        """
        Booleans are technically ints, so they can be converted to
            Decimals.
        """
        value = True
        self.assertFilterPasses(value, Decimal(value))

    def test_fail_invalid_value(self):
        """
        The incoming value cannot be converted to a Decimal.
        """
        self.assertFilterErrors(
            'this is not a decimal',
            [f.Decimal.CODE_INVALID],
        )

    def test_fail_non_finite_value(self):
        """
        Non-finite values like 'NaN' and 'Inf' are considered invalid,
            even though they are technically parseable.
        """
        self.assertFilterErrors( 'NaN', [f.Decimal.CODE_NON_FINITE])
        self.assertFilterErrors('+Inf', [f.Decimal.CODE_NON_FINITE])
        self.assertFilterErrors('-Inf', [f.Decimal.CODE_NON_FINITE])
        # There are a few other possible non-finite values out there,
        #   but you get the idea.

    def test_pass_tuple(self):
        """
        You may pass a 3-tuple for more control over how the resulting
            Decimal object is created.
        """
        value = (0, (4, 2), -1)
        self.assertFilterPasses(value, Decimal(value))

    def test_fail_tuple_invalid(self):
        """
        If you're going to use a tuple, you've got to make sure you get
            it right!
        """
        self.assertFilterErrors(('1', '2', '3'), [f.Decimal.CODE_INVALID])

    def test_fail_tuple_disallowed(self):
        """
        The filter is configured to disallow tuple values.
        """
        self.assertFilterErrors(
            self._filter((0, (4, 2), -1), allow_tuples=False),
            [f.Type.CODE_WRONG_TYPE],
        )

    def test_fail_bytes(self):
        """
        To ensure that the filter behaves the same in Python 2 and
          Python 3, bytes are not allowed.
        """
        self.assertFilterErrors(b'-12', [f.Type.CODE_WRONG_TYPE])

    def test_fail_unsupported_type(self):
        """
        The incoming value has an unsupported type.
        """
        self.assertFilterErrors(
            {0, (4, 2), -1},
            [f.Type.CODE_WRONG_TYPE],
        )


class EmptyTestCase(BaseFilterTestCase):
    filter_type = f.Empty

    def test_pass_none(self):
        """
        `None` shall pass.

        What?

        `None` shall pass!
        """
        self.assertFilterPasses(None)

    def test_pass_empty_string(self):
        """The incoming value is an empty string."""
        self.assertFilterPasses('')

    def test_pass_empty_collection(self):
        """The incoming value is a collection with length < 1."""
        self.assertFilterPasses([])
        self.assertFilterPasses({})
        self.assertFilterPasses(Lengthy(0))
        # etc.

    def test_fail_non_empty_string(self):
        """The incoming value is a non-empty string."""
        self.assertFilterErrors(
            'Goodbye world!',
            [f.Empty.CODE_NOT_EMPTY],
        )

    def test_fail_non_empty_collection(self):
        """The incoming value is a collection with length > 0."""
        # The values inside the collection may be empty, but the
        #   collection itself is not.
        self.assertFilterErrors(['', '', ''],   [f.Empty.CODE_NOT_EMPTY])
        self.assertFilterErrors({'': ''},       [f.Empty.CODE_NOT_EMPTY])
        self.assertFilterErrors(Lengthy(1),     [f.Empty.CODE_NOT_EMPTY])
        # etc.

    def test_fail_non_collection(self):
        """The incoming value does not have a length."""
        # The Filter can't determine the length of this object, so it
        #   assumes that it is not empty.
        self.assertFilterErrors(object(), [f.Empty.CODE_NOT_EMPTY])

    def test_zero_is_not_empty(self):
        """PHP developers take note!"""
        self.assertFilterErrors(0, [f.Empty.CODE_NOT_EMPTY])

    def test_false_is_not_empty(self):
        """
        The boolean value `False` is NOT considered empty because it
            represents SOME kind of value.
        """
        self.assertFilterErrors(False, [f.Empty.CODE_NOT_EMPTY])


class IntTestCase(BaseFilterTestCase):
    filter_type = f.Int

    def test_pass_none(self):
        """
        `None` always passes this Filter.

        Use `Required | Int` if you want to reject `None`.
        """
        self.assertFilterPasses(None)

    def test_pass_valid_int(self):
        """The incoming value can be interpreted as an int."""
        self.assertFilterPasses('42', 42)

    def test_pass_zero(self):
        """The incoming value is zero."""
        self.assertFilterPasses('0', 0)

    def test_pass_negative(self):
        """The incoming value is a negative int."""
        self.assertFilterPasses('-314', -314)

    def test_pass_boolean(self):
        """Booleans are technically ints."""
        self.assertFilterPasses(True, 1)

    def test_fail_invalid_value(self):
        """
        The incoming value cannot be interpreted as a number, let alone
            an integer.
        """
        self.assertFilterErrors(
            'this is not an int',
            [f.Decimal.CODE_INVALID],
        )

    def test_fail_bytes(self):
        """
        To ensure that the filter behaves the same in Python 2 and
          Python 3, bytes are not allowed.
        """
        self.assertFilterErrors(b'-12', [f.Type.CODE_WRONG_TYPE])

    def test_fail_float_value(self):
        """
        The incoming value contains significant digits after the
            decimal point.
        """
        self.assertFilterErrors(
            '42.01',
            [f.Int.CODE_DECIMAL],
        )

    def test_pass_int_point_zero(self):
        """
        The incoming value contains only insignificant digits after the
            decimal point.
        """
        self.assertFilterPasses('42.0000000000000', 42)

    def test_pass_scientific_notation(self):
        """The incoming value is expressed in scientific notation."""
        self.assertFilterPasses('2.6E4', 26000)

    def test_fail_non_finite_value(self):
        """The incoming value is a non-finite value."""
        self.assertFilterErrors( 'NaN', [f.Decimal.CODE_NON_FINITE])
        self.assertFilterErrors('+Inf', [f.Decimal.CODE_NON_FINITE])
        self.assertFilterErrors('-Inf', [f.Decimal.CODE_NON_FINITE])
        # There are a few other possible non-finite values out there,
        #   but you get the idea.

    def test_pass_int(self):
        """The incoming value is already an int object."""
        self.assertFilterPasses(777)


class MaxLengthTestCase(BaseFilterTestCase):
    filter_type = f.MaxLength

    def test_pass_none(self):
        """
        `None` always passes this Filter.

        Use `Required | MaxLength` if you want to reject `None`.
        """
        self.assertFilterPasses(
            self._filter(None, max_length=0),
        )

    def test_pass_short(self):
        """The incoming value is shorter than the max length."""
        self.assertFilterPasses(
            self._filter('Hello', max_length=6),
        )

    def test_pass_max_length(self):
        """The incoming value has the max allowed length."""
        self.assertFilterPasses(
            self._filter('World', max_length=5),
        )

    def test_fail_long(self):
        """The incoming value is longer than the max length."""
        self.assertFilterErrors(
            self._filter('Goodbye', max_length=5),
            [f.MaxLength.CODE_TOO_LONG],
        )

    def test_multi_byte_characters(self):
        """
        Multibyte characters are treated differently depending on
            whether you pass in a unicode or a byte string.
        """
        # "Hello world" in Chinese:
        decoded_value   = '\u4f60\u597d\u4e16\u754c'
        encoded_value   = decoded_value.encode('utf-8')


        # The string version of the string contains 4 code points.
        self.assertFilterPasses(
            self._filter(decoded_value, max_length=4),
        )

        # The bytes version of the string contains 12 bytes.
        self.assertFilterErrors(
            self._filter(encoded_value, max_length=4),
            [f.MaxLength.CODE_TOO_LONG],
        )

    def test_pass_short_collection(self):
        """
        The incoming value is a collection with length less than or
            equal to the max length.
        """
        self.assertFilterPasses(
            self._filter(['foo', 'bar', 'baz', 'luhrmann'], max_length=4),
        )

        self.assertFilterPasses(
            self._filter({'foo': 'bar', 'baz': 'luhrmann'}, max_length=3),
        )

        self.assertFilterPasses(
            self._filter(Lengthy(4), max_length=4),
        )

        # etc.

    def test_fail_long_collection(self):
        """
        The incoming value is a collection with length greater than the
            max length.
        """
        self.assertFilterErrors(
            self._filter(['foo', 'bar', 'baz', 'luhrmann'], max_length=3),
            [f.MaxLength.CODE_TOO_LONG],
        )

        self.assertFilterErrors(
            self._filter({'foo': 'bar', 'baz': 'luhrmann'}, max_length=1),
            [f.MaxLength.CODE_TOO_LONG],
        )

        self.assertFilterErrors(
            self._filter(Lengthy(4), max_length=3),
            [f.MaxLength.CODE_TOO_LONG],
        )

        # etc.


class MinLengthTestCase(BaseFilterTestCase):
    filter_type = f.MinLength

    def test_pass_none(self):
        """
        `None` always passes this Filter.

        Use `Required | MinLength` if you want to reject `None`.
        """
        self.assertFilterPasses(
            self._filter(None, min_length=5),
        )

    def test_pass_long(self):
        """
        The incoming value has length greater than the minimum value.
        """
        self.assertFilterPasses(
            self._filter('Hello', min_length=2),
        )

    def test_pass_min_length(self):
        """The incoming value has length equal to the minimum value."""
        self.assertFilterPasses(
            self._filter('World', min_length=5),
        )

    def test_fail_short(self):
        """
        The incoming value has length less than the minimum value.
        """
        self.assertFilterErrors(
            self._filter('Goodbye', min_length=10),
            [f.MinLength.CODE_TOO_SHORT],
        )

    def test_multi_byte_characters(self):
        """
        Multibyte characters are treated differently depending on
            whether you pass in a unicode or a byte string.
        """
        # "Hello world" in Chinese:
        decoded_value   = '\u4f60\u597d\u4e16\u754c'
        encoded_value   = decoded_value.encode('utf-8')

        # The string version of the string contains 4 code points.
        self.assertFilterErrors(
            self._filter(decoded_value, min_length=12),
            [f.MinLength.CODE_TOO_SHORT],
        )

        # The bytes version of the string contains 12 bytes.
        self.assertFilterPasses(
            self._filter(encoded_value, min_length=12),
        )

    def test_pass_long_collection(self):
        """
        The incoming value is a collection with length greater than or
            equal to the minimum value.
        """
        self.assertFilterPasses(
            self._filter(['foo', 'bar', 'baz', 'luhrmann'], min_length=3),
        )

        self.assertFilterPasses(
            self._filter({'foo': 'bar', 'baz': 'luhrmann'}, min_length=1),
        )

        self.assertFilterPasses(
            self._filter(Lengthy(6), min_length=5),
        )

        # etc.

    def test_fail_short_collection(self):
        """
        The incoming value is a collection with length less than the
            minimum value.
        """
        self.assertFilterErrors(
            self._filter(['foo', 'bar', 'baz', 'luhrmann'], min_length=5),
            [f.MinLength.CODE_TOO_SHORT],
        )

        self.assertFilterErrors(
            self._filter({'foo': 'bar', 'baz': 'luhrmann'}, min_length=3),
            [f.MinLength.CODE_TOO_SHORT],
        )

        self.assertFilterErrors(
            self._filter(Lengthy(6), min_length=7),
            [f.MinLength.CODE_TOO_SHORT],
        )

        # etc.


class NoOpTestCase(BaseFilterTestCase):
    filter_type = f.NoOp

    def test_pass_any_value(self):
        """
        You can pass any value you want to a NoOp, and it will pass.
        """
        self.assertFilterPasses('supercalafragalisticexpialadoshus')


class NotEmptyTestCase(BaseFilterTestCase):
    filter_type = f.NotEmpty

    def test_pass_none(self):
        """
        By default, `NotEmpty` will treat `None` as valid (just like
            every other Filter).
        """
        self.assertFilterPasses(None)

    def test_fail_none(self):
        """You can configure the filter to reject `None` values."""
        self.assertFilterErrors(
            self._filter(None, allow_none=False),
            [f.NotEmpty.CODE_EMPTY],
        )

    def test_pass_non_empty_string(self):
        """The incoming value is a non-empty string."""
        self.assertFilterPasses('Hello, world!')

    def test_pass_non_empty_collection(self):
        """
        The incoming value is a collection with length > 0.
        """
        # The values in the collection may be empty, but the collection
        #   itself is not.
        self.assertFilterPasses(['', '', ''])
        self.assertFilterPasses({'': ''})
        self.assertFilterPasses(Lengthy(1))
        # etc.

    def test_pass_non_collection(self):
        """The incoming value does not have a length."""
        self.assertFilterPasses(object())

    def test_fail_empty_string(self):
        """The incoming value is an empty string."""
        self.assertFilterErrors('', [f.NotEmpty.CODE_EMPTY])

    def test_fail_empty_collection(self):
        """The incoming value is a collection with length < 1."""
        self.assertFilterErrors([],         [f.NotEmpty.CODE_EMPTY])
        self.assertFilterErrors({},         [f.NotEmpty.CODE_EMPTY])
        self.assertFilterErrors(Lengthy(0), [f.NotEmpty.CODE_EMPTY])
        # etc.

    def test_zero_is_not_empty(self):
        """PHP developers take note!"""
        self.assertFilterPasses(0)

    def test_false_is_not_empty(self):
        """
        The boolean value `False` is NOT considered empty because it
            represents SOME kind of value.
        """
        self.assertFilterPasses(False)


class OptionalTestCase(BaseFilterTestCase):
    filter_type = f.Optional

    def test_pass_none(self):
        """
        It'd be pretty silly to name a Filter "Optional" if it rejects
            `None`, wouldn't it?
        """
        self.assertFilterPasses(None)

    def test_replace_none(self):
        """
        The default replacement value is `None`, but you can change it
            to something else.
        """
        self.assertFilterPasses(
            self._filter(None, default='Hello, world!'),
            'Hello, world!',
        )

    def test_replace_empty_string(self):
        """The incoming value is an empty string."""
        self.assertFilterPasses(
            self._filter('', default='42'),
            '42',
        )

    def test_replace_empty_collection(self):
        """The incoming value is a collection with length < 1."""
        # By default, the Filter will replace empty values with `None`.
        self.assertFilterPasses([],         None)
        self.assertFilterPasses({},         None)
        self.assertFilterPasses(Lengthy(0), None)
        # etc.

    def test_pass_non_empty_string(self):
        """The incoming value is a non-empty string."""
        self.assertFilterPasses(
            self._filter('Goodbye, world!', default='fail')
        )

    def test_pass_non_empty_collection(self):
        """The incoming value is a collection with length > 0."""
        # The values inside the collection may be empty, but the
        #   collection itself is not.
        self.assertFilterPasses(['', '', ''])
        self.assertFilterPasses({'': ''})
        self.assertFilterPasses(Lengthy(12))
        # etc.

    def test_pass_non_collection(self):
        """Any value that doesn't have a length is left alone."""
        self.assertFilterPasses(
            self._filter(object(), default='fail'),
        )

    def test_zero_is_not_empty(self):
        """PHP developers take note!"""
        self.assertFilterPasses(
            self._filter(0, default='fail'),
        )

    def test_false_is_not_empty(self):
        """
        The boolean value `False` is NOT considered empty because it
            represents SOME kind of value.
        """
        self.assertFilterPasses(
            self._filter(False, default='fail'),
        )


class RequiredTestCase(BaseFilterTestCase):
    filter_type = f.Required

    def test_fail_none(self):
        """Required is the only filter that does not allow `None`."""
        self.assertFilterErrors(None, [f.Required.CODE_EMPTY])

    def test_pass_non_empty_string(self):
        """The incoming value is a non-empty string."""
        self.assertFilterPasses('Hello, world!')

    def test_pass_non_empty_collection(self):
        """The incoming value is a collection with length > 0."""
        # The values in the collection may be empty, but the collection
        #   itself is not.
        self.assertFilterPasses(['', '', ''])
        self.assertFilterPasses({'': ''})
        self.assertFilterPasses(Lengthy(1))
        # etc.

    def test_pass_non_collection(self):
        """Any value that does not have a length passes."""
        self.assertFilterPasses(object())

    def test_fail_empty_string(self):
        """The incoming value is an empty string."""
        self.assertFilterErrors('', [f.Required.CODE_EMPTY])

    def test_fail_empty_collection(self):
        """The incoming value is a collection with length < 1."""
        self.assertFilterErrors([],         [f.Required.CODE_EMPTY])
        self.assertFilterErrors({},         [f.Required.CODE_EMPTY])
        self.assertFilterErrors(Lengthy(0), [f.Required.CODE_EMPTY])
        # etc.

    def test_zero_is_not_empty(self):
        """PHP developers take note!"""
        self.assertFilterPasses(0)

    def test_false_is_not_empty(self):
        """
        The boolean value `False` is NOT considered empty because it
            represents SOME kind of value.
        """
        self.assertFilterPasses(False)


class TypeTestCase(BaseFilterTestCase):
    filter_type = f.Type

    def test_pass_none(self):
        """
        `None` always passes this Filter.

        Use `Required | Type` if you want to reject `None`.
        """
        self.assertFilterPasses(
            self._filter(None, allowed_types=text_type),
        )

    def test_pass_matching_type(self):
        """The incoming value has the expected type."""
        self.assertFilterPasses(
            self._filter('Hello, world!', allowed_types=text_type),
        )

    def test_fail_non_matching_type(self):
        """The incoming value does not have the expected type."""
        self.assertFilterErrors(
            self._filter(b'Not a string, sorry.', allowed_types=text_type),
            [f.Type.CODE_WRONG_TYPE],
        )

    def test_multiple_allowed_types(self):
        """You can configure the Filter to allow multiple types."""
        self.assertFilterPasses(
            self._filter('Hello, world!', allowed_types=(text_type, int)),
        )

        self.assertFilterPasses(
            self._filter(42, allowed_types=(text_type, int)),
        )

        self.assertFilterErrors(
            self._filter(b'Not a unicode.', allowed_types=(text_type, int)),
            [f.Type.CODE_WRONG_TYPE],
        )

    def test_pass_subclass(self):
        """The incoming value's type is a subclass of an allowed type."""
        self.assertFilterPasses(
            # bool is a subclass of int.
            self._filter(True, allowed_types=int),
        )

    def test_fail_subclass(self):
        """You can configure the Filter to require exact type matches."""
        self.assertFilterErrors(
            self._filter(True, allowed_types=int, allow_subclass=False),
            [f.Type.CODE_WRONG_TYPE],
        )

    def test_fail_types_are_not_instances(self):
        """
        The Filter checks that the value is an INSTANCE of its allowed
            type(s).  It will reject the type(s) themselves.
        """
        self.assertFilterErrors(
            self._filter(text_type, allowed_types=text_type),
            [f.Type.CODE_WRONG_TYPE],
        )


class UnicodeTestCase(BaseFilterTestCase):
    filter_type = f.Unicode

    def test_pass_none(self):
        """
        `None` always passes this Filter.

        Use `Required | Unicode` if you want to reject `None`.
        """
        self.assertFilterPasses(None)

    def test_pass_unicode(self):
        """The incoming value is a unicode."""
        self.assertFilterPasses('┻━┻︵ \(°□°)/ ︵ ┻━┻ ') # RAWR!

    def test_pass_bytes_utf8(self):
        """
        The incoming value is a byte string that is encoded as UTF-8.
        """
        self.assertFilterPasses(
            # You get used to it.
            # I don't even see the code.
            # All I see is, "blond"... "brunette"... "redhead"...
            # Hey, you uh... want a drink?
            b'\xe2\x99\xaa '
            b'\xe2\x94\x8f(\xc2\xb0.\xc2\xb0)\xe2\x94\x9b '
            b'\xe2\x94\x97(\xc2\xb0.\xc2\xb0)\xe2\x94\x93 '
            b'\xe2\x99\xaa',

            '♪ ┏(°.°)┛ ┗(°.°)┓ ♪',
        )

    def test_fail_bytes_non_utf8(self):
        """
        The incoming value is a byte string that is encoded using a
            codec other than UTF-8.

        Note that there is no such thing as a unicode object with
            the "wrong encoding".

        :see: https://docs.python.org/2/howto/unicode.html
        """
        # How about something a bit more realistic for this test?
        #   Like the Swedish word for 'Apple'.
        # noinspection SpellCheckingInspection
        incoming = b'\xc4pple'

        self.assertFilterErrors(
            incoming,
            [f.Unicode.CODE_DECODE_ERROR],
        )

        # In order for this to work, we have to tell the Filter what
        #   encoding to use:
        self.assertFilterPasses(
            self._filter(incoming, encoding='iso-8859-1'),
            'Äpple',
        )

    def test_pass_string_like_object(self):
        """
        The incoming value is an object that can be cast as a string.
        """
        value = '／人 ⌒ ‿‿ ⌒ 人＼' # Squee!

        self.assertFilterPasses(
            Unicody(value),
            value,
        )

    def test_pass_bytes_like_object(self):
        """
        The incoming value is an object that can be cast as a byte
            string.
        """
        self.assertFilterPasses(
            Bytesy(b'(\xe2\x99\xa5\xe2\x80\xbf\xe2\x99\xa5)'),

            # I can almost hear the sappy music now.
            '(♥‿♥)',
        )

    def test_pass_boolean(self):
        """The incoming value is a boolean (treated as an int)."""
        self.assertFilterPasses(True, '1')

    def test_pass_decimal_with_scientific_notation(self):
        """
        The incoming value is a Decimal that was parsed from scientific
            notation.
        """
        # Note that `text_type(Decimal('2.8E6')` yields '2.8E+6', which
        #   is not what we want!
        self.assertFilterPasses(
            Decimal('2.8E6'),
            '2800000',
        )

    def test_pass_xml_element(self):
        """The incoming value is an ElementTree XML Element."""
        self.assertFilterPasses(
            Element('foobar'),
            '<foobar />',
        )

    def test_unicode_normalization(self):
        """
        The Filter always returns the NFC form of the unicode string.

        :see: https://en.wikipedia.org/wiki/Unicode_equivalence
        :see: http://stackoverflow.com/q/16467479
        """
        #   U+0065 LATIN SMALL LETTER E
        # + U+0301 COMBINING ACUTE ACCENT
        # (2 code points)
        decomposed  = 'Ame\u0301lie'

        # U+00E9 LATIN SMALL LETTER E WITH ACUTE
        # (1 code point)
        composed    = 'Am\xe9lie'

        self.assertFilterPasses(decomposed, composed)

    def test_unicode_normalization_disabled(self):
        """You can force the Filter not to perform normalization."""
        decomposed  = 'Ame\u0301lie'

        self.assertFilterPasses(
            self._filter(decomposed, normalize=False),
            decomposed,
        )

    def test_remove_non_printables(self):
        """
        By default, this Filter also removes non-printable characters
            (both ASCII and Unicode varieties).
        """
        self.assertFilterPasses(
            # \x00-\x1f are ASCII control characters.
            # \xef\xbf\xbf is the Unicode control character \uffff,
            #   encoded as UTF-8.
            b'\x10Hell\x00o,\x1f wor\xef\xbf\xbfld!',

            'Hello, world!',
        )

    def test_remove_non_printables_disabled(self):
        """
        You can force the Filter not to remove non-printable characters.
        """
        self.assertFilterPasses(
            self._filter(
                b'\x10Hell\x00o,\x1f wor\xef\xbf\xbfld!',
                normalize = False,
            ),

            '\u0010Hell\u0000o,\u001f wor\uffffld!',
        )

    def test_newline_normalization(self):
        """
        By default, any newlines in the string are automatically
            converted to unix-style ('\n').
        """
        self.assertFilterPasses(
            b'unix\n - windows\r\n - weird\r\r\n',
            'unix\n - windows\n - weird\n\n',
        )

    def test_newline_normalization_disabled(self):
        """You can force the Filter not to normalize line endings."""
        self.assertFilterPasses(
            self._filter(
                b'unix\n - windows\r\n - weird\r\r\n',
                normalize = False,
            ),

            'unix\n - windows\r\n - weird\r\r\n',
        )
