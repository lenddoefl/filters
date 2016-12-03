# coding=utf-8
from __future__ import absolute_import, division, print_function, \
    unicode_literals

from decimal import Decimal, ROUND_CEILING

import filters as f
from filters.test import BaseFilterTestCase


class MaxTestCase(BaseFilterTestCase):
    filter_type = f.Max

    def test_pass_none(self):
        """
        `None` always passes this Filter.

        Use `Required | Max` if you want to reject `None`.
        """
        self.assertFilterPasses(
            self._filter(None, max_value=5),
        )

    def test_pass_lesser_value(self):
        """
        The incoming value is smaller than the max value.
        """
        self.assertFilterPasses(
            self._filter(3, max_value=5),
        )

    def test_pass_equal_value(self):
        """
        The incoming value is equal to the max value.
        """
        self.assertFilterPasses(
            self._filter(5, max_value=5),
        )

    def test_fail_equal_value_exclusive_comparison(self):
        """
        The incoming value is equal to the max value, but the Filter is
            configured to use an exclusive comparison.

        This is useful for infinite-precision floats and other cases
            where it is impossible to specify the max value exactly.
        """
        self.assertFilterErrors(
            # The Filter is configured to allow any float value that is
            #   less than - but not equal to - 5.0.
            self._filter(5.0, max_value=5.0, exclusive=True),
            [f.Max.CODE_TOO_BIG],
        )

    def test_fail_greater_value(self):
        """
        The incoming value is greater than the max value.
        """
        self.assertFilterErrors(
            self._filter(8, max_value=5),
            [f.Max.CODE_TOO_BIG],
        )

    def test_string_comparison_oddness(self):
        """
        If the filter is being used on strings, the comparison is case
            sensitive.

        Note:  due to the way ASCII works, this may yield unexpected
            results (lowercase > uppercase).  Also, watch out for
            Unicode oddness!

        Basically what I'm trying to say is, don't use this Filter on
            string values.
        """
        # ord('F') => 70
        # ord('f') => 102
        self.assertFilterErrors(
            self._filter('foo', max_value='Foo'),
            [f.Max.CODE_TOO_BIG],
        )

    def test_fail_wrong_type(self):
        """
        If the value has a different type than the max value, it fails.

        Be sure to leverage other filters (e.g., Int) to ensure that
            the incoming value has the correct type.
        """
        # Ints and strings are not compatible.
        self.assertFilterErrors(
            self._filter('4', max_value=5),
            [f.Type.CODE_WRONG_TYPE]
        )

        # Also not compatible: ints and floats.
        self.assertFilterErrors(
            self._filter(4.99, max_value=5),
            [f.Type.CODE_WRONG_TYPE],
        )

        # Even though bool is a subclass of int, it still won't work.
        #   It's gotta be an exact type match!
        self.assertFilterErrors(
            self._filter(True, max_value=5),
            [f.Type.CODE_WRONG_TYPE],
        )

        # Floats and Decimals don't play nice, either.
        self.assertFilterErrors(
            self._filter(Decimal('4'), max_value=4.5),
            [f.Type.CODE_WRONG_TYPE],
        )


class MinTestCase(BaseFilterTestCase):
    filter_type = f.Min

    def test_pass_none(self):
        """
        `None` always passes this Filter.

        Use `Required | Min` if you want to reject `None`.
        """
        self.assertFilterPasses(
            self._filter(None, min_value=5),
        )

    def test_pass_greater_value(self):
        """
        The incoming value is greater than the min value.
        """
        self.assertFilterPasses(
            self._filter(8, min_value=5),
        )

    def test_pass_equal_value(self):
        """
        The incoming value is equal to the min value.
        """
        self.assertFilterPasses(
            self._filter(5, min_value=5),
        )

    def test_fail_equal_value_exclusive_comparison(self):
        """
        The incoming value is equal to the min value, but the Filter is
            configured to use exclusive comparison.

        This is useful for infinite-precision floats and other cases
            where it is impossible to specify the min value exactly.
        """
        self.assertFilterErrors(
            # The Filter is configured to allow any float value that is
            #   greater than - but not equal to - 5.0.
            self._filter(5.0, min_value=5.0, exclusive=True),
            [f.Min.CODE_TOO_SMALL],
        )

    def test_fail_lesser_value(self):
        """
        The incoming value is less than the min value.
        """
        self.assertFilterErrors(
            self._filter(4, min_value=5),
            [f.Min.CODE_TOO_SMALL],
        )

    def test_string_comparison_oddness(self):
        """
        If the filter is being used on strings, the comparison is case
            sensitive.

        Note:  due to the way ASCII works, this may yield unexpected
            results (lowercase > uppercase).  Also, watch out for
            Unicode oddness!

        Basically what I'm trying to say is, don't use this Filter on
            string values.
        """
        # ord('f') => 102
        # ord('F') => 70
        self.assertFilterErrors(
            self._filter('Foo', min_value='foo'),
            [f.Min.CODE_TOO_SMALL],
        )

    def test_fail_wrong_type(self):
        """
        If the value has a different type than the max value, it fails.

        Be sure to leverage other filters (e.g., Int) to ensure that
            the incoming value has the correct type.
        """
        # Ints and strings are not compatible.
        self.assertFilterErrors(
            self._filter('6', min_value=5),
            [f.Type.CODE_WRONG_TYPE],
        )

        # Also not compatible: ints and floats.
        self.assertFilterErrors(
            self._filter(5.01, min_value=5),
            [f.Type.CODE_WRONG_TYPE],
        )

        # Even though bool is a subclass of int, it still won't work.
        #   It's gotta be an exact type match!
        self.assertFilterErrors(
            self._filter(True, min_value=0),
            [f.Type.CODE_WRONG_TYPE],
        )

        # Floats and Decimals don't play nice, either.
        self.assertFilterErrors(
            self._filter(Decimal('3.14'), min_value=2.5),
            [f.Type.CODE_WRONG_TYPE],
        )


class RoundTestCase(BaseFilterTestCase):
    filter_type = f.Round

    def test_pass_none(self):
        """
        `None` always passes this filter.

        Use `Required | Round` to reject incoming `None`.
        """
        self.assertFilterPasses(None)

    def test_pass_round_integer_to_nearest_integer(self):
        """
        Rounds an integer to the nearest integer value.
        """
        self.assertFilterPasses(
            # You should always specify `to_nearest` as a string, to
            #   avoid floating point issues.
            self._filter(42, to_nearest='5'),

            # The result is always a Decimal object.
            Decimal('40.0'),
        )

    def test_pass_round_integer_to_nearest_float(self):
        """
        Rounds an integer to the nearest float value.
        """
        self.assertFilterPasses(
            self._filter(42, to_nearest='5.5'),

            Decimal('44.0'),
        )

    def test_pass_round_float_to_nearest_integer(self):
        """
        Rounds a float to the nearest integer value.
        """
        self.assertFilterPasses(
            self._filter(3.5, to_nearest='1'),
            Decimal('4.0'),
        )

    def test_pass_round_float_to_nearest_float(self):
        """
        Rounds a float to the nearest float value.
        """
        # Just to be tricky, use a float value that would normally
        #   result in some nasty floating point artifacts.
        # :see: http://stackoverflow.com/a/4340355
        self.assertFilterPasses(
            self._filter(1.368161685161, to_nearest='0.05'),
            Decimal('1.35'),
        )

    def test_pass_round_string_float(self):
        """
        Rounds a float represented as a string to avoid floating point
            issues.
        """
        # :see: http://stackoverflow.com/q/22599883
        self.assertFilterPasses(
            self._filter('2.775', to_nearest='0.1'),
            Decimal('2.8'),
        )

    def test_pass_round_to_big_value(self):
        """
        Rounds something to a value greater than 1.
        """
        self.assertFilterPasses(
            self._filter('386.428', to_nearest='20'),
            Decimal('380'),
        )

    def test_pass_round_negative_value(self):
        """
        Rounds a negative value.
        """
        self.assertFilterPasses(
            self._filter('-2.775', to_nearest='0.1'),
            Decimal('-2.8'),
        )

    def test_pass_modify_rounding(self):
        """
        By default, the filter will round up any value that is halfway
            to the nearest `to_nearest` value, but this behavior can be
            customized.
        """
        self.assertFilterPasses(
            self._filter('0.00000000001', rounding=ROUND_CEILING),
            Decimal('1'),
        )

    def test_pass_custom_result_type(self):
        """
        You can customize the return type of the filter.
        """
        self.assertFilterPasses(
            self._filter('2.775', result_type=int),
            3,
        )

    def test_fail_wrong_type(self):
        """
        The incoming value is not numeric.
        """
        self.assertFilterErrors('three', [f.Decimal.CODE_INVALID])
