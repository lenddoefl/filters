import json
import typing
from datetime import date, datetime, time, tzinfo

from dateutil.parser import parse as dateutil_parse
from dateutil.tz import tzoffset
from pytz import utc

from filters.base import BaseFilter, Type
from filters.number import Int, Max, Min

__all__ = [
    'Array',
    'ByteArray',
    'Call',
    'Choice',
    'Date',
    'Datetime',
    'Empty',
    'Length',
    'MaxLength',
    'MinLength',
    'NoOp',
    'NotEmpty',
    'Optional',
    'Required',
]


class Array(Type):
    """
    Validates that the incoming value is a non-string sequence.
    """

    def __init__(
            self,
            aliases: typing.Optional[typing.Mapping[type, str]] = None,
    ) -> None:
        super().__init__(typing.Sequence, True, aliases)

    def _apply(self, value):
        value = super()._apply(value)  # type: typing.Sequence

        if self._has_errors:
            return None

        if isinstance(value, (bytes, str)):
            return self._invalid_value(
                value=value,
                reason=self.CODE_WRONG_TYPE,

                template_vars={
                    'incoming': self.get_type_name(type(value)),
                    'allowed':  self.get_allowed_type_names(),
                },
            )

        return value


class ByteArray(BaseFilter):
    """
    Converts an incoming value into a bytearray.
    """
    CODE_BAD_ENCODING = 'bad_encoding'

    templates = {
        CODE_BAD_ENCODING:
            'Unable to encode this value using {encoding}.',
    }

    def __init__(self, encoding: str = 'utf-8') -> None:
        """
        :param encoding:
            The encoding to use when decoding strings into bytes.
        """
        super().__init__()

        self.encoding = encoding

    def _apply(self, value):
        value = self._filter(value, Type(typing.Iterable))

        if self._has_errors:
            return None

        if isinstance(value, bytearray):
            return value

        if isinstance(value, bytes):
            return bytearray(value)

        if isinstance(value, str):
            try:
                return bytearray(value, encoding=self.encoding)
            except UnicodeEncodeError:
                return self._invalid_value(
                    value=value,
                    reason=self.CODE_BAD_ENCODING,

                    template_vars={
                        'encoding': self.encoding,
                    },
                )

        from filters.complex import FilterRepeater
        filtered = self._filter(value, FilterRepeater(
            # Only allow ints and booleans.
            Type(int) |
            # Convert booleans to int (Min and Max require an
            # exact type match).
            Int |
            # Min value for each byte is 2^0-1.
            Min(0) |
            # Max value for each byte is 2^8-1.
            Max(255)
        ))

        if self._has_errors:
            return None

        return bytearray(filtered)


class Call(BaseFilter):
    """
    Runs the value through a callable.

    Usually, creating a custom filter type works better, as you have
    more control over how invalid values are handled, you can specify
    custom error codes, it's easier to write tests for, etc.

    But, in a pinch, this is a handy way to quickly integrate a custom
    function into a filter chain.
    """

    def __init__(self,
            callable_: typing.Callable[..., typing.Any],
            *extra_args,
            **extra_kwargs
    ) -> None:
        """
        :param callable_:
            The callable that will be applied to incoming values.

        :param extra_args:
            Extra positional arguments to pass to the callable.

        :param extra_kwargs:
            Extra keyword arguments to pass to the callable.
        """
        super().__init__()

        self.callable = callable_
        self.extra_args = extra_args
        self.extra_kwargs = extra_kwargs

    def _apply(self, value):
        try:
            return self.callable(value, *self.extra_args, **self.extra_kwargs)
        except Exception as e:
            return self._invalid_value(
                value,
                reason=e,
                exc_info=True,
            )


class Choice(BaseFilter):
    """
    Expects the value to match one of the items in a set.

    Note:  When matching string values, the comparison is case-
    sensitive!  Use the :py:class:`CaseFold` Filter if you want to
    perform a case-insensitive comparison.
    """
    CODE_INVALID = 'not_valid_choice'

    templates = {
        CODE_INVALID: 'Valid options are: {choices}',
    }

    def __init__(self, choices: typing.Iterable[typing.Hashable]) -> None:
        super().__init__()

        self.choices = set(choices)

    def __str__(self):
        return '{type}({choices!r})'.format(
            type=type(self).__name__,
            choices=json.dumps(sorted(self.choices)),
        )

    def _apply(self, value):
        if value not in self.choices:
            return self._invalid_value(
                value=value,
                reason=self.CODE_INVALID,
                exc_info=True,

                template_vars={
                    'choices': sorted(self.choices),
                },
            )

        return value


class Datetime(BaseFilter):
    """
    Interprets the value as a UTC datetime.
    """
    CODE_INVALID = 'not_datetime'

    templates = {
        CODE_INVALID:
            'This value does not appear to be a datetime.',
    }

    def __init__(
            self,
            timezone: typing.Optional[typing.Union[tzinfo, int, float]] = None,
            naive: bool = False,
    ) -> None:
        """
        :param timezone:
            Specifies the timezone to use when the *incoming* value is
            a naive timestamp.  Has no effect on timezone-aware
            timestamps.

            IMPORTANT:  The result is always converted to UTC,
            regardless of the value of the ``timezone`` param!

            You can provide an int/float here, which is the offset from
            UTC in hours (e.g., 5 = UTC+5).

        :param naive:
            If True, the filter will *return* naive datetime objects
            (sans tzinfo).  This is useful e.g., for datetimes that
            will be stored in a database that doesn't understand aware
            timestamps.

            IMPORTANT:  Incoming values are still converted to UTC
            before stripping tzinfo!
        """
        super().__init__()

        if not isinstance(timezone, tzinfo):
            if timezone in [0, None]:
                timezone = utc
            else:
                # Assume that we got an int/float instead.
                timezone = tzoffset(
                    name='UTC{offset:+}'.format(offset=timezone),
                    offset=float(timezone) * 3600.0,
                )

        self.timezone = timezone
        self.naive = naive

    def __str__(self):
        return '{type}(timezone={timezone!r}, naive={naive!r})'.format(
            type=type(self).__name__,
            timezone=self.timezone,
            naive=self.naive,
        )

    def _apply(self, value):
        if isinstance(value, datetime):
            parsed = value
        elif isinstance(value, date):
            # http://stackoverflow.com/a/1937636
            parsed = datetime.combine(value, time.min)
        else:
            try:
                #
                # It's a shame we can't pass ``tzinfos`` to
                # :py:meth:`dateutil_parse.parse`; ``tzinfos`` only has
                # effect if we also specify ``ignoretz = True``, which
                # we definitely don't want to do here!
                #
                # https://dateutil.readthedocs.org/en/latest/parser.html#dateutil.parser.parse
                #
                parsed = dateutil_parse(value)
            except ValueError:
                return self._invalid_value(
                    value=value,
                    reason=self.CODE_INVALID,
                    exc_info=True,
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

        filtered = super()._apply(value)  # type: datetime

        # Normally we return `None` if we get any errors, but in this
        # case, we'll let the superclass method decide.
        return filtered if self._has_errors else filtered.date()


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


class Length(BaseFilter):
    """
    Ensures incoming values have exactly the right length.
    """
    CODE_TOO_LONG = 'too_long'
    CODE_TOO_SHORT = 'too_short'

    templates = {
        CODE_TOO_LONG:
            'Value is too long (length must be exactly {expected}).',
        CODE_TOO_SHORT:
            'Value is too short (length must be exactly {expected}).',
    }

    def __init__(self, length: int) -> None:
        super().__init__()

        self.length = length

    def __str__(self):
        return '{type}(length={length!r})'.format(
            type=type(self).__name__,
            length=self.length,
        )

    def _apply(self, value):
        value = self._filter(value, Type(typing.Sized))

        if self._has_errors:
            return None

        if len(value) > self.length:
            return self._invalid_value(
                value=value,
                reason=self.CODE_TOO_LONG,

                template_vars={
                    'expected': self.length,
                },
            )
        elif len(value) < self.length:
            return self._invalid_value(
                value=value,
                reason=self.CODE_TOO_SHORT,

                template_vars={
                    'expected': self.length,
                },
            )

        return value


class MaxLength(BaseFilter):
    """
    Enforces a maximum length on the value.
    """
    CODE_TOO_LONG = 'too_long'

    templates = {
        CODE_TOO_LONG: 'Value is too long (length must be < {max}).',
    }

    def __init__(self, max_length: int) -> None:
        super().__init__()

        self.max_length = max_length

    def __str__(self):
        return '{type}({max_length!r})'.format(
            type=type(self).__name__,
            max_length=self.max_length,
        )

    def _apply(self, value):
        if len(value) > self.max_length:
            # Note that we do not truncate the value:
            #   - It's not always clear which end we should truncate
            #     from.
            #   - We should keep this filter's behavior consistent with
            #     that of MinLength.
            return self._invalid_value(
                value=value,
                reason=self.CODE_TOO_LONG,

                template_vars={
                    'length': len(value),
                    'max':    self.max_length,
                },
            )

        return value


class MinLength(BaseFilter):
    """
    Enforces a minimum length on the value.
    """
    CODE_TOO_SHORT = 'too_short'

    templates = {
        CODE_TOO_SHORT: 'Value is too short (length must be > {min}).',
    }

    def __init__(self, min_length: int) -> None:
        super().__init__()

        self.min_length = min_length

    def __str__(self):
        return '{type}({min_length!r})'.format(
            type=type(self).__name__,
            min_length=self.min_length,
        )

    def _apply(self, value):
        if len(value) < self.min_length:
            #
            # Note that we do not pad the value:
            #   - It is not clear to which end(s) we should add the
            #     padding.
            #   - It is not clear what the padding value(s) should be.
            #   - We should keep this filter's behavior consistent with
            #     that of MaxLength.
            #
            return self._invalid_value(
                value=value,
                reason=self.CODE_TOO_SHORT,

                template_vars={
                    'length': len(value),
                    'min':    self.min_length,
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


class NotEmpty(BaseFilter):
    """
    Expects the value not to be empty.

    In this context, "empty" is defined as having zero length.  Note
    that this filter considers values that do not have length to be
    not empty (in particular, False and 0 are not considered empty
    here).

    By default, this filter treats ``None`` as valid, just like every
    other filter.  However, you can configure the filter to reject
    ``None`` in its initializer method.
    """
    CODE_EMPTY = 'empty'

    templates = {
        CODE_EMPTY: 'Non-empty value expected.',
    }

    def __init__(self, allow_none: bool = True) -> None:
        """
        :param allow_none:
            Whether to allow ``None``.
        """
        super().__init__()

        self.allow_none = allow_none

    def __str__(self):
        return '{type}(allow_none={allow_none!r})'.format(
            type=type(self).__name__,
            allow_none=self.allow_none,
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
    Same as NotEmpty, but with ``allow_none`` hard-wired to ``False``.

    This filter is the only exception to the "``None`` passes by
    default" rule.
    """
    templates = {
        NotEmpty.CODE_EMPTY: 'This value is required.',
    }

    def __init__(self):
        super().__init__(allow_none=False)


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
        :param default:
            The default value used to replace empty values.
        """
        super().__init__()

        self.default = default

    def __str__(self):
        return '{type}(default={default!r})'.format(
            type=type(self).__name__,
            default=self.default,
        )

    def _apply(self, value):
        try:
            length = len(value)
        except TypeError:
            length = 1

        return value if length > 0 else self.default

    def _apply_none(self):
        return self.default
