# coding=utf-8
from __future__ import absolute_import, division, print_function, \
    unicode_literals

import json
import unicodedata
from datetime import date, datetime, time, tzinfo
from decimal import Decimal as DecimalType, InvalidOperation
from typing import Hashable, Iterable, Sized, Text, Union
from xml.etree.ElementTree import Element, tostring

# noinspection PyCompatibility
import regex
from dateutil.parser import parse as dateutil_parse
from dateutil.tz import tzoffset
from pytz import utc
from six import (
    PY2,
    PY3,
    binary_type,
    python_2_unicode_compatible,
    text_type,
)

from filters import BaseFilter, Min, Max, Type

__all__ = [
    'ByteArray',
    'ByteString',
    'Choice',
    'Date',
    'Datetime',
    'Decimal',
    'Empty',
    'Int',
    'Length',
    'MaxLength',
    'MinLength',
    'NoOp',
    'NotEmpty',
    'Optional',
    'Required',
    'Unicode',
]


class ByteArray(BaseFilter):
    """Converts an incoming value into a bytearray."""
    CODE_BAD_ENCODING = 'bad_encoding'

    templates = {
        CODE_BAD_ENCODING:
            'Unable to encode this value using {encoding}.',
    }

    def __init__(self, encoding='utf-8'):
        # type: (Text) -> None
        """
        :param encoding: The encoding to use when converting strings.
        """
        super(ByteArray, self).__init__()

        self.encoding = encoding

    def _apply(self, value):
        value = self._filter(value, Type(Iterable))

        if self._has_errors:
            return None

        if isinstance(value, bytearray):
            return value

        if isinstance(value, binary_type):
            return bytearray(value)

        if isinstance(value, text_type):
            try:
                return bytearray(value, encoding=self.encoding)
            except UnicodeEncodeError:
                return self._invalid_value(
                    value           = value,
                    reason          = self.CODE_BAD_ENCODING,
                    template_vars   = {
                        'encoding':     self.encoding,
                    },
                )

        from filters import FilterRepeater
        filtered = self._filter(value, FilterRepeater(
                # Only allow ints and booleans.
                Type(int)
                # Convert booleans to int (Min and Max require an
                #   exact type match).
                | Int
                # Min value for each byte is 2^0-1.
                | Min(0)
                # Max value for each byte is 2^8-1.
                | Max(255)
        ))

        if self._has_errors:
            return None

        return bytearray(filtered)


@python_2_unicode_compatible
class Choice(BaseFilter):
    """
    Expects the value to match one of the items in a set.

    Note:  When matching string values, the comparison is case-
        sensitive!  Use the `CaseFold` Filter if you want to perform a
        case-insensitive comparison.
    """
    CODE_INVALID = 'not_valid_choice'

    templates = {
        CODE_INVALID: 'Valid options are: {choices}',
    }

    def __init__(self, choices):
        # type: (Iterable[Hashable]) -> None
        super(Choice, self).__init__()

        self.choices = set(choices)

    def __str__(self):
        return '{type}({choices!r})'.format(
            type = type(self).__name__,

            # Use JSON to mask Python syntax (e.g., remove "u" prefix
            #   on unicode strings in Python 2).
            # :see: Type.__init__
            choices = json.dumps(sorted(self.choices)),
        )

    def _apply(self, value):
        if value not in self.choices:
            return self._invalid_value(
                value           = value,
                reason          = self.CODE_INVALID,
                exc_info        = True,

                template_vars   = {
                    'choices': sorted(self.choices),
                },
            )

        return value


@python_2_unicode_compatible
class Datetime(BaseFilter):
    """
    Interprets the value as a UTC datetime.
    """
    CODE_INVALID = 'not_datetime'

    templates = {
        CODE_INVALID:
            'This value does not appear to be a datetime.',
    }

    def __init__(self, timezone=None, naive=False):
        # type: (Union[tzinfo, int, float], bool) -> None
        """
        :param timezone: Specifies the timezone to use when the
            INCOMING value is a naive timestamp.  Has no effect on
            timezone-aware timestamps.

            Note that the result is always converted to UTC, regardless
            of the value of the `timezone` param!

            You can provide an int/float, which is the offset from UTC
            in hours (e.g., 5 = UTC+5).

        :param naive: If True, the filter will RETURN naive datetime
            objects (sans tzinfo).  This is useful e.g., for datetimes
            that will be stored in a database.

            Note that the result is still converted to UTC before
            removing its tzinfo!
        """
        super(Datetime, self).__init__()

        if not isinstance(timezone, tzinfo):
            if timezone in [0, None]:
                timezone = utc
            else:
                # Assume that we got an int/float instead.
                timezone = tzoffset(
                    name    = 'UTC{offset:+}'.format(offset=timezone),
                    offset  = float(timezone) * 3600.0,
                )

        self.timezone   = timezone
        self.naive      = naive

    def __str__(self):
        return '{type}(timezone={timezone!r}, naive={naive!r})'.format(
            type        = type(self).__name__,
            timezone    = self.timezone,
            naive       = self.naive,
        )

    def _apply(self, value):
        if isinstance(value, datetime):
            parsed = value
        elif isinstance(value, date):
            # :see: http://stackoverflow.com/a/1937636
            parsed = datetime.combine(value, time.min)
        else:
            try:
                #
                # It's a shame we can't pass `tzinfos` to
                #   `dateutil.parser.parse`; `tzinfos` only has effect
                #   if we also specify `ignoretz = True`, which we
                #   don't want to do here.
                #
                # :see: https://dateutil.readthedocs.org/en/latest/parser.html#dateutil.parser.parse
                #
                # Note that this method will raise a ValueError if the
                #   value cannot be parsed.
                #
                parsed = dateutil_parse(value)
            except ValueError:
                return self._invalid_value(
                    value       = value,
                    reason      = self.CODE_INVALID,
                    exc_info    = True,
                )

        if not parsed.tzinfo:
            parsed = parsed.replace(tzinfo=self.timezone)

        # Always covert to UTC.
        aware_result = parsed.astimezone(utc)

        return (
            aware_result.replace(tzinfo=None)
                if self.naive
                else aware_result
        )


class Date(Datetime):
    """
    Interprets the value as a UTC date.

    Note that the value is first converted to a datetime with UTC
        timezone, which may cause the resulting date to appear to be
        off by +/- 1 day (does not apply if the value is already a date
        object).
    """
    CODE_INVALID = 'not_date'

    templates = {
        CODE_INVALID: 'This value does not appear to be a date.',
    }

    def _apply(self, value):
        if isinstance(value, date) and not isinstance(value, datetime):
            return value

        filtered = super(Date, self)._apply(value) # type: datetime

        # Normally we return `None` if we get any errors, but in this
        #   case, we'll let the superclass method decide.
        return filtered if self._has_errors else filtered.date()


@python_2_unicode_compatible
class Decimal(BaseFilter):
    """Interprets the value as a Decimal object."""
    CODE_INVALID    = 'not_numeric'
    CODE_NON_FINITE = 'not_finite'

    templates = {
        CODE_INVALID:       'Numeric value expected.',
        CODE_NON_FINITE:    'Numeric value expected.',
    }

    def __init__(self, max_precision=None, allow_tuples=True):
        # type: (int, bool) -> None
        """
        :param max_precision: Max number of decimal places the
            resulting value is allowed to have.  Values that are too
            precise will be rounded to fit.

        :param allow_tuples: Whether to allow tuple-like inputs.
            Allowing tuple inputs might couple the implementation more
            tightly to Python's Decimal type, so you have the option
            to disallow it.
        """
        super(Decimal, self).__init__()

        self.max_precision  = max_precision
        self.allow_tuples   = allow_tuples

    def __str__(self):
        return '{type}(max_precision={max_precision!r})'.format(
            type            = type(self).__name__,
            max_precision   = self.max_precision,
        )

    def _apply(self, value):
        allowed_types = (text_type, int, float, DecimalType,)
        if self.allow_tuples:
            # Python's Decimal type supports both tuples and lists.
            # :see: decimal.Decimal.__init__
            allowed_types += (list, tuple,)

        value = self._filter(value, Type(allowed_types))

        if self._has_errors:
            return value

        try:
            d = DecimalType(value)
        except (InvalidOperation, TypeError, ValueError):
            return self._invalid_value(value, self.CODE_INVALID, exc_info=True)

        # Decimal's constructor also accepts values such as 'NaN' or
        #   '+Inf', which aren't valid in this context.
        # :see: decimal.Decimal._parser
        if not d.is_finite():
            return self._invalid_value(
                value       = value,
                reason      = self.CODE_NON_FINITE,
                exc_info    = True,
            )

        if self.max_precision is not None:
            d = d.quantize(DecimalType('.1') ** self.max_precision)

        return d


class Empty(BaseFilter):
    """
    Expects the value to be empty.

    In this context, "empty" is defined as having zero length.  Note
        that this Filter considers values that do not have length to be
        not empty (in particular, False and 0 are not considered empty
        here).
    """
    CODE_NOT_EMPTY = 'not_empty'

    templates = {
        CODE_NOT_EMPTY: 'Empty value expected.',
    }

    def _apply(self, value):
        try:
            length = len(value)
        except TypeError:
            length = 1

        return (
            self._invalid_value(value, self.CODE_NOT_EMPTY)
                if length
                else value
        )


class Int(BaseFilter):
    """
    Interprets the value as an int.

    Strings and other compatible values will be converted, but floats
        will be treated as INVALID.

    Note that Python handles really, really big int values
        transparently, so you don't need to worry about overflow.
    :see: http://stackoverflow.com/a/538583
    """
    CODE_DECIMAL = 'not_int'

    templates = {
        CODE_DECIMAL: 'Integer value expected.',
    }

    def _apply(self, value):
        decimal = self._filter(value, Decimal) # type: DecimalType

        if self._has_errors:
            return None

        # Do not allow floats.
        # :see: http://stackoverflow.com/a/19965088
        if decimal % 1:
            return self._invalid_value(value, self.CODE_DECIMAL)

        return int(decimal)


@python_2_unicode_compatible
class Length(BaseFilter):
    """Ensures incoming values have exactly the right length."""
    CODE_TOO_LONG   = 'too_long'
    CODE_TOO_SHORT  = 'too_short'

    templates = {
        CODE_TOO_LONG:
            'Value is too long (length must be exactly {expected}).',
        CODE_TOO_SHORT:
            'Value is too short (length must be exactly {expected}).',
    }

    def __init__(self, length):
        # type: (int) -> None
        super(Length, self).__init__()

        self.length = length

    def __str__(self):
        return '{type}(length={length!r})'.format(
            type    = type(self).__name__,
            length  = self.length,
        )

    def _apply(self, value):
        value = self._filter(value, Type(Sized))

        if self._has_errors:
            return None

        if len(value) > self.length:
            return self._invalid_value(
                value           = value,
                reason          = self.CODE_TOO_LONG,

                template_vars = {
                    'expected': self.length,
                },
            )
        elif len(value) < self.length:
            return self._invalid_value(
                value           = value,
                reason          = self.CODE_TOO_SHORT,

                template_vars = {
                    'expected': self.length,
                },
            )

        return value


@python_2_unicode_compatible
class MaxLength(BaseFilter):
    """Enforces a maximum length on the value."""
    CODE_TOO_LONG = 'too_long'

    templates = {
        CODE_TOO_LONG: 'Value is too long (length must be < {max}).',
    }

    def __init__(self, max_length):
        # type: (int) -> None
        super(MaxLength, self).__init__()

        self.max_length = max_length

    def __str__(self):
        return '{type}({max_length!r})'.format(
            type        = type(self).__name__,
            max_length  = self.max_length,
        )

    def _apply(self, value):
        if len(value) > self.max_length:
            #
            # Note that we do not truncate the value:
            #   - It's not always clear which end we should truncate
            #       from.
            #   - We should keep this Filter's behavior consistent with
            #       that of MinLength.
            #
            return self._invalid_value(
                value           = value,
                reason          = self.CODE_TOO_LONG,

                template_vars = {
                    'length':       len(value),
                    'max':          self.max_length,
                },
            )

        return value


class MinLength(BaseFilter):
    """Enforces a minimum length on the value."""
    CODE_TOO_SHORT = 'too_short'

    templates = {
        CODE_TOO_SHORT: 'Value is too short (length must be > {min}).',
    }

    def __init__(self, min_length):
        # type: (int) -> None
        super(MinLength, self).__init__()

        self.min_length = min_length

    def __str__(self):
        return '{type}({min_length!r})'.format(
            type        = type(self).__name__,
            min_length  = self.min_length,
        )

    def _apply(self, value):
        if len(value) < self.min_length:
            #
            # Note that we do not pad the value:
            #   - It is not clear to which end(s) we should add the
            #       padding.
            #   - It is not clear what the padding value(s) should be.
            #   - We should keep this Filter's behavior consistent with
            #       that of MaxLength.
            #
            return self._invalid_value(
                value           = value,
                reason          = self.CODE_TOO_SHORT,

                template_vars = {
                    'length':       len(value),
                    'min':          self.min_length,
                },
            )

        return value


class NoOp(BaseFilter):
    """
    Filter that does nothing, used when you need a placeholder Filter
        in a FilterChain.
    """
    def _apply(self, value):
        return value


@python_2_unicode_compatible
class NotEmpty(BaseFilter):
    """
    Expects the value not to be empty.

    In this context, "empty" is defined as having zero length.  Note
        that this Filter considers values that do not have length to be
        not empty (in particular, False and 0 are not considered empty
        here).

    By default, this Filter treats `None` as valid, just like every
        other Filter.  However, you can configure the Filter to reject
        `None` in its initializer method.
    """
    CODE_EMPTY = 'empty'

    templates = {
        CODE_EMPTY: 'Non-empty value expected.',
    }

    def __init__(self, allow_none=True):
        # type: (bool) -> None
        """
        :param allow_none: Whether to allow `None`.
        """
        super(NotEmpty, self).__init__()

        self.allow_none = allow_none

    def __str__(self):
        return '{type}(allow_none={allow_none!r})'.format(
            type        = type(self).__name__,
            allow_none  = self.allow_none,
        )

    def _apply(self, value):
        try:
            length = len(value)
        except TypeError:
            length = 1

        return value if length else self._invalid_value(value, self.CODE_EMPTY)

    def _apply_none(self):
        if not self.allow_none:
            return self._invalid_value(None, self.CODE_EMPTY)

        return None


class Required(NotEmpty):
    """
    Same as NotEmpty, but with `allow_none` hard-wired to `False`.

    This Filter is the only exception to the "`None` passes by default"
        rule.
    """
    templates = {
        NotEmpty.CODE_EMPTY: 'This value is required.',
    }

    def __init__(self):
        super(Required, self).__init__(allow_none=False)


@python_2_unicode_compatible
class Optional(BaseFilter):
    """
    Changes empty and null values into a default value.

    In this context, "empty" is defined as having zero length.  Note
        that this Filter considers values that do not have length to be
        not empty (in particular, False and 0 are not considered empty
        here).
    """
    def __init__(self, default=None):
        """
        :param default: The default value used to replace empty values.
        """
        super(Optional, self).__init__()

        self.default = default

    def __str__(self):
        return '{type}(default={default!r})'.format(
            type    = type(self).__name__,
            default = self.default,
        )

    def _apply(self, value):
        try:
            length = len(value)
        except TypeError:
            length = 1

        return value if length > 0 else self.default

    def _apply_none(self):
        return self.default


@python_2_unicode_compatible
class Unicode(BaseFilter):
    """
    Converts a value into a unicode string.

    Note:  By default, additional normalization is applied to the
        resulting value.  See the initializer docstring for more info.

    :see: https://docs.python.org/2/howto/unicode.html
    :see: https://en.wikipedia.org/wiki/Unicode_equivalence
    """
    CODE_DECODE_ERROR = 'wrong_encoding'

    templates = {
        CODE_DECODE_ERROR: 'This value cannot be decoded using {encoding}.',
    }

    def __init__(self, encoding='utf-8', normalize=True):
        # type: (Text, bool) -> None
        """
        :param encoding: Used to decode non-unicode values.

        :param normalize: Whether to normalize the resulting value:
            - Convert to NFC form.
            - Remove non-printable characters.
            - Convert all line endings to unix-style ('\n').
        """
        super(Unicode, self).__init__()

        self.encoding   = encoding
        self.normalize  = normalize

        if self.normalize:
            #
            # Compile the regex that we will use to remove non-
            #   printables from the resulting unicode.
            # :see: http://www.regular-expressions.info/unicode.html#category
            #
            # Note: using a double negative so that we can exclude
            #   newlines, which are technically considered control
            #   chars.
            # :see: http://stackoverflow.com/a/3469155
            #
            self.npr = regex.compile(r'[^\P{C}\s]+', regex.UNICODE)

    def __str__(self):
        return '{type}(encoding={encoding!r})'.format(
            type        = type(self).__name__,
            encoding    = self.encoding,
        )

    def _apply(self, value):
        try:
            if isinstance(value, text_type):
                decoded = value

            elif isinstance(value, binary_type):
                decoded = value.decode(self.encoding)

            elif isinstance(value, bool):
                decoded = text_type(int(value))

            # :kludge: In Python 3, bytes(<int>) does weird things.
            # :see: https://www.python.org/dev/peps/pep-0467/
            elif isinstance(value, (int, float)):
                decoded = text_type(value)

            elif isinstance(value, DecimalType):
                decoded = format(value, 'f')

            elif isinstance(value, Element):
                # :kludge: There's no way (that I know of) to get
                #   `ElementTree.tostring` to return a unicode.
                decoded = tostring(value, 'utf-8').decode('utf-8')

            elif (
                    PY2 and hasattr(value, '__str__')
                or  PY3 and hasattr(value, '__bytes__')
            ):
                decoded = binary_type(value).decode(self.encoding)

            else:
                decoded = text_type(value)
        except UnicodeDecodeError:
            return self._invalid_value(
                value           = value,
                reason          = self.CODE_DECODE_ERROR,
                exc_info        = True,

                template_vars = {
                    'encoding': self.encoding,
                },
            )

        if self.normalize:
            return (
                # Return the final string in composed form.
                # :see: :see: https://en.wikipedia.org/wiki/Unicode_equivalence
                unicodedata.normalize('NFC',
                    # Remove non-printables.
                    self.npr.sub('', decoded)
                )
                    # Normalize line endings.
                    # :see: http://stackoverflow.com/a/1749887
                    .replace('\r\n', '\n')
                    .replace('\r', '\n')
            )
        else:
            return decoded


class ByteString(Unicode):
    """
    Converts a value into a byte string, encoded as UTF-8.

    IMPORTANT:  This Filter returns string objects, not bytearrays!
    """
    def __init__(self, encoding='utf-8', normalize=False):
        # type: (Text, bool) -> None
        """
        :param encoding: Used to decode non-unicode values.

        :param normalize: Whether to normalize the unicode value before
            converting back into bytes:
            - Convert to NFC form.
            - Remove non-printable characters.
            - Convert all line endings to unix-style ('\n').

        Note that `normalize` is `False` by default for Bytes, but
        `True` by default for Unicode.
        """
        super(ByteString, self).__init__(encoding, normalize)

    # noinspection SpellCheckingInspection
    def _apply(self, value):
        decoded = super(ByteString, self)._apply(value) # type: Text

        #
        # No need to catch UnicodeEncodeErrors here; UTF-8 can handle
        #   any unicode value.
        #
        # Technically, we could get this error if we encounter a code
        #   point beyond U+10FFFF (the highest valid code point in the
        #   Unicode standard).
        #
        # However, it's not possible to create a `unicode` object with
        #   an invalid code point, so we wouldn't even be able to get
        #   this far if the incoming value contained a character that
        #   can't be represented using UTF-8.
        #
        # Note that in some versions of Python, it is possible (albeit
        #   really difficult) to trick Python into creating unicode
        #   objects with invalid code points, but it generally requires
        #   using specific codecs that aren't UTF-8.
        #
        # Example of exploit and release notes from the Python release
        #   (2.7.6) that fixes the issue:
        # :see: https://gist.github.com/rspeer/7559750
        # :see: https://hg.python.org/cpython/raw-file/99d03261c1ba/Misc/NEWS
        #

        # Normally we return `None` if we get any errors, but in this
        #   case, we'll let the superclass method decide.
        return decoded if self._has_errors else decoded.encode('utf-8')
