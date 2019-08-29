from decimal import Decimal, ROUND_CEILING

import filters as f
from filters.test import BaseFilterTestCase


class DecimalTestCase(BaseFilterTestCase):
    filter_type = f.Decimal

    def test_pass_none(self):
        """
        `None` always passes this Filter.

        Use `Required | Decimal` if you want to reject `None`.
        """
        self.assertFilterPasses(None)

    def test_pass_valid_decimal(self):
        """
        The incoming value can be interpreted as a Decimal.
        """
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

    def test_max_precision_quantized(self):
        """
        ``max_precision`` can also be specified as a Decimal object.
        """
        self.assertFilterPasses(
            self._filter('3.1415926', max_precision=Decimal('0.001')),
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
        self.assertFilterErrors('NaN', [f.Decimal.CODE_NON_FINITE])
        self.assertFilterErrors('+Inf', [f.Decimal.CODE_NON_FINITE])
        self.assertFilterErrors('-Inf', [f.Decimal.CODE_NON_FINITE])
        # There are a few other possible non-finite values out there,
        # but you get the idea.

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
        self.assertFilterErrors(('1', '2', '3'), [
            f.Decimal.CODE_INVALID])

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


class IntTestCase(BaseFilterTestCase):
    filter_type = f.Int

    def test_pass_none(self):
        """
        `None` always passes this Filter.

        Use `Required | Int` if you want to reject `None`.
        """
        self.assertFilterPasses(None)

    def test_pass_valid_int(self):
        """
        The incoming value can be interpreted as an int.
        """
        self.assertFilterPasses('42', 42)

    def test_pass_zero(self):
        """
        The incoming value is zero.
        """
        self.assertFilterPasses('0', 0)

    def test_pass_negative(self):
        """
        The incoming value is a negative int.
        """
        self.assertFilterPasses('-314', -314)

    def test_pass_boolean(self):
        """
        Booleans are technically ints.
        """
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
        """
        The incoming value is expressed in scientific notation.
        """
        self.assertFilterPasses('2.6E4', 26000)

    def test_fail_non_finite_value(self):
        """
        The incoming value is a non-finite value.
        """
        self.assertFilterErrors('NaN', [f.Decimal.CODE_NON_FINITE])
        self.assertFilterErrors('+Inf', [f.Decimal.CODE_NON_FINITE])
        self.assertFilterErrors('-Inf', [f.Decimal.CODE_NON_FINITE])
        # There are a few other possible non-finite values out there,
        # but you get the idea.

    def test_pass_int(self):
        """
        The incoming value is already an int object.
        """
        self.assertFilterPasses(777)


class MaxTestCase(BaseFilterTestCase):
    filter_type = f.Max

    def test_pass_none(self):
        """
        ``None`` always passes this Filter.

        Use ``Required | Max`` if you want to reject ``None``.
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
            # less than - but not equal to - 5.0.
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

        Basically what I'm trying to say is, don't use this filter on
        string values.
        """
        # ord('F') => 70
        # ord('f') => 102
        self.assertFilterErrors(
            self._filter('foo', max_value='Foo'),
            [f.Max.CODE_TOO_BIG],
        )


class MinTestCase(BaseFilterTestCase):
    filter_type = f.Min

    def test_pass_none(self):
        """
        ``None`` always passes this Filter.

        Use ``Required | Min`` if you want to reject ``None``.
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

        Basically what I'm trying to say is, don't use this filter on
        string values.
        """
        # ord('f') => 102
        # ord('F') => 70
        self.assertFilterErrors(
            self._filter('Foo', min_value='foo'),
            [f.Min.CODE_TOO_SMALL],
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
            # avoid floating point issues.
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
        # result in some nasty floating point artifacts.
        # http://stackoverflow.com/a/4340355
        self.assertFilterPasses(
            self._filter(1.368161685161, to_nearest='0.05'),
            Decimal('1.35'),
        )

    def test_pass_round_string_float(self):
        """
        Rounds a float represented as a string to avoid floating point
        issues.
        """
        # http://stackoverflow.com/q/22599883
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
