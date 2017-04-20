# coding=utf-8
from __future__ import absolute_import, division, print_function, \
    unicode_literals

from decimal import Decimal as DecimalType, InvalidOperation, ROUND_HALF_UP

from six import python_2_unicode_compatible, text_type
from typing import Any, Text, Union

from filters.base import BaseFilter, Type

__all__ = [
    'Decimal',
    'Int',
    'Max',
    'Min',
    'Round',
]


@python_2_unicode_compatible
class Decimal(BaseFilter):
    """
    Interprets the value as a :py:class:`decimal.Decimal` object.
    """
    CODE_INVALID    = 'not_numeric'
    CODE_NON_FINITE = 'not_finite'

    templates = {
        CODE_INVALID:       'Numeric value expected.',
        CODE_NON_FINITE:    'Numeric value expected.',
    }

    def __init__(self, max_precision=None, allow_tuples=True):
        # type: (Union[int, DecimalType], bool) -> None
        """
        :param max_precision:
            Max number of decimal places the resulting value is allowed
            to have.  Values that are too precise will be rounded to
            fit.

            To avoid ambiguity, specify ``max_precision`` as a
            ``decimal.Decimal`` object.

            For example, to round to the nearest 1/100::

                Decimal(max_precision=decimal.Decimal('0.01'))

        :param allow_tuples:
            Whether to allow tuple-like inputs.

            Allowing tuple inputs might couple the implementation more
            tightly to Python's Decimal type, so you have the option
            to disallow it.
        """
        super(Decimal, self).__init__()

        # Convert e.g., 3 => DecimalType('.001').
        if not (
                    (max_precision is None)
                or  isinstance(max_precision, DecimalType)
        ):
            max_precision = DecimalType('.1') ** max_precision

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
            # :py:meth:`decimal.Decimal.__init__`
            allowed_types += (list, tuple,)

        value = self._filter(value, Type(allowed_types))

        if self._has_errors:
            return value

        try:
            d = DecimalType(value)
        except (InvalidOperation, TypeError, ValueError):
            return self._invalid_value(value, self.CODE_INVALID, exc_info=True)

        # Decimal's constructor also accepts values such as 'NaN' or
        # '+Inf', which aren't valid in this context.
        # :see: decimal.Decimal._parser
        if not d.is_finite():
            return self._invalid_value(
                value       = value,
                reason      = self.CODE_NON_FINITE,
                exc_info    = True,
            )

        if self.max_precision is not None:
            d = d.quantize(self.max_precision)

        return d


class Int(BaseFilter):
    """
    Interprets the value as an int.

    Strings and other compatible values will be converted, but floats
    will be treated as INVALID.

    Note that Python handles really, really big int values
    transparently, so you don't need to worry about overflow.

    References:
      - http://stackoverflow.com/a/538583
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
        # http://stackoverflow.com/a/19965088
        if decimal % 1:
            return self._invalid_value(value, self.CODE_DECIMAL)

        # Once we get to this point, we're pretty confident that we've
        # got something that can be converted into an int.
        # noinspection PyTypeChecker
        return int(decimal)


@python_2_unicode_compatible
class Max(BaseFilter):
    """
    Enforces a maximum value.

    Note:  Technically, this filter can operate on any type that
    supports comparison, but it tends to be used exclusively with
    numeric types.
    """
    CODE_TOO_BIG = 'too_big'

    templates = {
        CODE_TOO_BIG: 'Value is too large (must be {operator} {max}).',
    }

    def __init__(self, max_value, exclusive=False):
        # type: (Any, bool) -> None
        """
        :param max_value:
            The max value that the Filter will accept.

        :param exclusive:
            Whether to exclude the max value itself as a valid value:

            - True: The incoming value must be _less than_ the max value.
            - False (default): The incoming value must be _less than
              or equal to_ the max value.
        """
        super(Max, self).__init__()

        self.max_value  = max_value
        self.exclusive  = exclusive

    def __str__(self):
        return (
            '{type}({max_value!r}, exclusive={exclusive!r})'.format(
                type        = type(self).__name__,
                max_value   = self.max_value,
                exclusive   = self.exclusive,
            )
        )

    def _apply(self, value):
        # Note that this will yield weird results for string values.
        # We could add better unicode support, if we ever need it.
        # http://stackoverflow.com/q/1097908
        if (
                (value > self.max_value)
            or  (self.exclusive and (value == self.max_value))
        ):
            return self._invalid_value(
                value   = value,
                reason  = self.CODE_TOO_BIG,

                # This only makes sense if `self.exclusive` is False.
                # Better to be consistent and replace all invalid
                # values with `None`.
                # replacement = self.max_value,

                template_vars = {
                    'operator': '<' if self.exclusive else '<=',
                    'max':      self.max_value,
                },
            )

        return value


@python_2_unicode_compatible
class Min(BaseFilter):
    """
    Enforces a minimum value.

    Note:  Technically, this filter can operate on any type that
    supports comparison, but it tends to be used exclusively with
    numeric types.
    """
    CODE_TOO_SMALL  = 'too_small'

    templates = {
        CODE_TOO_SMALL: 'Value is too small (must be {operator} {min}).',
    }

    def __init__(self, min_value, exclusive=False):
        # type: (Any, bool) -> None
        """
        :param min_value:
            The min value that the Filter will accept.

        :param exclusive:
            Whether to exclude the min value itself as a valid value:

            - True: The incoming value must be _greater than_ the min
              value.
            - False (default): The incoming value must be _greater than
              or equal to_ the min value.
        """
        super(Min, self).__init__()

        self.min_value  = min_value
        self.exclusive  = exclusive

    def __str__(self):
        return (
            '{type}({min_value!r}, exclusive={exclusive!r})'.format(
                type        = type(self).__name__,
                min_value   = self.min_value,
                exclusive   = self.exclusive,
            )
        )

    def _apply(self, value):
        # Note that this will yield weird results for string values.
        # We could add better unicode support, if we ever need it.
        # http://stackoverflow.com/q/1097908
        if (
                (value < self.min_value)
            or  (self.exclusive and (value == self.min_value))
        ):
            return self._invalid_value(
                value   = value,
                reason  = self.CODE_TOO_SMALL,

                # This only makes sense if ``self.exclusive`` is False.
                # Better to be consistent and replace all invalid
                # values with ``None``.
                # replacement = self.min_value,

                template_vars = {
                    'operator': '>' if self.exclusive else '>=',
                    'min':      self.min_value,
                },
            )

        return value


class Round(BaseFilter):
    """
    Rounds incoming values to whole numbers or decimals.
    """
    def __init__(self,
            to_nearest  = 1,
            rounding    = ROUND_HALF_UP,
            result_type = DecimalType,
    ):
        # type: (Union[int, Text, DecimalType], Text, type) -> None
        """
        :param to_nearest:
            The value that the filter should round to.

            E.g., ``Round(1)`` rounds to the nearest whole number.

            If you want to round to a float value, it is recommended
            that you provide it as a string or Decimal, to avoid
            floating point problems.

        :param rounding:
            Controls how to round values.

        :param result_type:
            The type of result to return.
        """
        super(Round, self).__init__()

        self.to_nearest = DecimalType(to_nearest)

        # Rounding to negative values isn't supported.
        # I'm not even sure if that concept is valid.
        Min(DecimalType('0')).apply(self.to_nearest)

        self.result_type    = result_type
        self.rounding       = rounding

    def _apply(self, value):
        value = self._filter(value, Decimal) # type: DecimalType

        if self._has_errors:
            return None

        one = DecimalType('1')

        # Scale, round, unscale.
        # Note that we use :py:meth:`decimal.Decimal.quantize` instead
        # of :py:func:`round` to avoid floating-point precision errors.
        # http://stackoverflow.com/a/4340355
        return self.result_type(
                (value * one / self.to_nearest)
                    .quantize(one, rounding=self.rounding)

            *   self.to_nearest
        )
