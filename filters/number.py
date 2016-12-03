# coding=utf-8
from __future__ import absolute_import, division, print_function, \
    unicode_literals

from decimal import Decimal as DecimalType, ROUND_HALF_UP

from six import python_2_unicode_compatible
from typing import Any, Text, Union

from filters import BaseFilter, Type

__all__ = [
    'Max',
    'Min',
    'Round',
]


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
        :param max_value: The max value that the Filter will use.
            Note that the incoming value must have the same type as the
            max value, or else it will automatically fail!

        :param exclusive: Whether to exclude the max value itself as a
            valid value:
            - True: The incoming value must be LESS THAN the max value.
            - False (default): The incoming value must be LESS THAN
                OR EQUAL TO the max value.
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
        value = self._filter(
            value,
            Type(type(self.max_value), allow_subclass=False),
        )

        if self._has_errors:
            return None

        # Note that this will yield weird results for string values.
        # We could add better unicode support, if we ever need it.
        # :see: http://stackoverflow.com/q/1097908
        if (
                (value > self.max_value)
            or  (self.exclusive and (value == self.max_value))
        ):
            return self._invalid_value(
                value   = value,
                reason  = self.CODE_TOO_BIG,

                # This only makes sense if `self.exclusive` is False.
                #   Better to be consistent and replace all invalid
                #   values with `None`.
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
        :param min_value: The min value that the Filter will use.
            Note that the incoming value must have the same type as the
            min value, or else it will automatically fail!

        :param exclusive: Whether to exclude the min value itself as a
            valid value:
            - True: The incoming value must be GREATER THAN the min
                value.
            - False (default): The incoming value must be GREATER THAN
                OR EQUAL TO the min value.
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
        value = self._filter(
            value,
            Type(type(self.min_value), allow_subclass=False),
        )

        if self._has_errors:
            return None

        # Note that this will yield weird results for string values.
        # We could add better unicode support, if we ever need it.
        # :see: http://stackoverflow.com/q/1097908
        if (
                (value < self.min_value)
            or  (self.exclusive and (value == self.min_value))
        ):
            return self._invalid_value(
                value   = value,
                reason  = self.CODE_TOO_SMALL,

                # This only makes sense if `self.exclusive` is False.
                #   Better to be consistent and replace all invalid
                #   values with `None`.
                # replacement = self.min_value,

                template_vars = {
                    'operator': '>' if self.exclusive else '>=',
                    'min':      self.min_value,
                },
            )

        return value


class Round(BaseFilter):
    """Rounds incoming values to whole numbers or decimals."""
    def __init__(self,
            to_nearest  = 1,
            rounding    = ROUND_HALF_UP,
            result_type = DecimalType,
    ):
        # type: (Union[int, Text, DecimalType], Text, type) -> None
        """
        :param to_nearest: The value that the filter should round to.
            E.g., `Round(1)` rounds to the nearest whole number.

            If you want to round to a float value, it is recommended
            that you provide it as a string or Decimal, to avoid
            floating point problems.

        :param rounding: Controls how to round values.

        :param result_type: The type of result to return.
        """
        super(Round, self).__init__()

        self.to_nearest = DecimalType(to_nearest)

        # Rounding to negative values isn't supported.
        # I'm not even sure if that concept is valid.
        Min(DecimalType('0')).apply(self.to_nearest)

        self.result_type    = result_type
        self.rounding       = rounding

    def _apply(self, value):
        from filters import Decimal
        value = self._filter(value, Decimal) # type: DecimalType

        if self._has_errors:
            return None

        one = DecimalType('1')

        # Scale, round, unscale.
        # Note that we use `DecimalType.quantize` instead of `round` to
        #   avoid floating-point precision errors.
        # :see: http://stackoverflow.com/a/4340355/5568265
        return self.result_type(
                (value * one / self.to_nearest)
                    .quantize(one, rounding=self.rounding)

            *   self.to_nearest
        )
