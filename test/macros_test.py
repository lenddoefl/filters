# coding=utf-8
from __future__ import absolute_import, division, print_function, \
    unicode_literals

from datetime import datetime
from unittest import TestCase

from pytz import utc

import filters as f
import filters.base
import filters.macros
import filters.string


class FilterMacroTestCase(TestCase):
    """Unit tests for `filter_macro`."""
    def test_decorator(self):
        """
        A common use case for Filter macros is to use them as
            decorators for functions.
        """
        @filters.macros.filter_macro
        def MyFilter():
            return filters.string.Unicode | f.Strip | f.MinLength(12)

        # As you would expect, invoking the macro returns a
        #   FilterChain.
        the_filter = MyFilter()

        self.assertEqual(
            the_filter.apply('  Hello, world!  '),
            'Hello, world!',
        )

        with self.assertRaises(filters.base.FilterError):
            the_filter.apply('Hi there!')

    def test_chain(self):
        """
        You can chain Filter macros with other Filters, the same as you
            would with any other Filter.
        """
        @filters.macros.filter_macro
        def MyFilter():
            return filters.string.Unicode | f.Strip | f.MinLength(12)

        # Note that you don't have to invoke the macro to include it in
        #   a chain.
        # If you don't believe me, try removing the decorator from
        #   `MyFilter`, and watch this test explode.
        filter_chain = MyFilter | f.Split(r'\s+')

        self.assertEqual(
            filter_chain.apply('Hello, world!'),
            ['Hello,', 'world!'],
        )

        with self.assertRaises(filters.base.FilterError):
            filter_chain.apply('Hi there!')

    def test_chain_macros(self):
        """
        Yup, you can chain Filter macros together, too.
        """
        @filters.macros.filter_macro
        def Filter1():
            return filters.string.Unicode | f.Strip

        @filters.macros.filter_macro
        def Filter2():
            return f.Split(r'\s+') | f.MinLength(2)

        filter_chain = Filter1 | Filter2

        self.assertEqual(
            filter_chain.apply('  Hello, world!  '),
            ['Hello,', 'world!'],
        )

        with self.assertRaises(filters.base.FilterError):
            filter_chain.apply('whazzup!')

    def test_partial(self):
        """
        You can use Filter macros to create partials from other Filter
            types.
        """
        MyDatetime = filters.macros.filter_macro(f.Datetime, timezone=12)

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
