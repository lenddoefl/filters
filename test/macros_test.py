from datetime import datetime
from unittest import TestCase

from pytz import utc

import filters as f
from filters.macros import FilterMacroType, filter_macro


class FilterMacroTestCase(TestCase):
    """
    Unit tests for :py:func:`filter_macro`.
    """

    def test_decorator(self):
        """
        A common use case for Filter macros is to use them as
        decorators for functions.
        """

        @filter_macro
        def MyFilter():
            return f.Unicode | f.Strip | f.MinLength(12)

        # You can use :py:class:`FilterMacroType` to detect a filter
        # macro.
        self.assertTrue(issubclass(MyFilter, FilterMacroType))

        # As you would expect, invoking the macro returns a
        # FilterChain.
        the_filter = MyFilter()

        self.assertNotIsInstance(the_filter, FilterMacroType)
        self.assertIsInstance(the_filter, f.FilterChain)

        self.assertEqual(
            the_filter.apply('  Hello, world!  '),
            'Hello, world!',
        )

        with self.assertRaises(f.FilterError):
            the_filter.apply('Hi there!')

    def test_chain(self):
        """
        You can chain Filter macros with other Filters, the same as you
        would with any other Filter.
        """

        @filter_macro
        def MyFilter():
            return f.Unicode | f.Strip | f.MinLength(12)

        # Note that you don't have to invoke the macro to include it in
        # a chain.
        # If you don't believe me, try removing the decorator from
        # ``MyFilter``, and watch this test explode.
        filter_chain = MyFilter | f.Split(r'\s+')

        self.assertEqual(
            filter_chain.apply('Hello, world!'),
            ['Hello,', 'world!'],
        )

        with self.assertRaises(f.FilterError):
            filter_chain.apply('Hi there!')

    def test_chain_macros(self):
        """
        Yup, you can chain Filter macros together, too.
        """

        @filter_macro
        def Filter1():
            return f.Unicode | f.Strip

        @filter_macro
        def Filter2():
            return f.Split(r'\s+') | f.MinLength(2)

        filter_chain = Filter1 | Filter2

        self.assertEqual(
            filter_chain.apply('  Hello, world!  '),
            ['Hello,', 'world!'],
        )

        with self.assertRaises(f.FilterError):
            filter_chain.apply('whazzup!')

    def test_decorator_optional_parameters(self):
        """
        A filter macro may accept optional parameters.
        """

        @filter_macro
        def MyFilter(min_length=12):
            return f.Unicode | f.MinLength(min_length)

        # `MyFilter` is configured to require 12 chars by default.
        filter_chain = f.Required | MyFilter

        self.assertEqual(
            filter_chain.apply('Hello, world!'),
            'Hello, world!',
        )

        with self.assertRaises(f.FilterError):
            filter_chain.apply('Hi there!')

    def test_partial(self):
        """
        You can use Filter macros to create partials from other Filter
        types.
        """
        MyDatetime = filter_macro(f.Datetime, timezone=12)

        self.assertEqual(
            MyDatetime().apply('2015-10-13 15:22:18'),

            # By default, MyDatetime assumes a timezone of UTC+12...
            datetime(2015, 10, 13, 3, 22, 18, tzinfo=utc),
        )

        self.assertEqual(
            # ... however, we can override it.
            MyDatetime(timezone=6).apply('2015-10-13 15:22:18'),

            datetime(2015, 10, 13, 9, 22, 18, tzinfo=utc),
        )
