# coding=utf-8
from __future__ import absolute_import, unicode_literals

import json
from itertools import starmap
from pprint import pformat
from traceback import format_exception
from typing import Any, Callable, Mapping, Sequence
from unittest import TestCase

from collections import OrderedDict
from six import iterkeys, string_types

from filters.base import BaseFilter
from filters.handlers import FilterRunner

__all__ = [
    'BaseFilterTestCase',
]


def sorted_dict(value):
    # type: (Mapping) -> Any
    """
    Sorts a dict's keys to avoid leaking information about the
    backend's handling of unordered dicts.
    """
    if isinstance(value, Mapping):
        return OrderedDict(
            (key, sorted_dict(value[key]))
                for key in sorted(iterkeys(value))
        )

    elif isinstance(value, Sequence) and not isinstance(value, string_types):
        return list(map(sorted_dict, value))

    else:
        return value


class BaseFilterTestCase(TestCase):
    """
    Base functionality for request filter unit tests.

    Prevents typos from causing invalid test passes/failures by
    abstracting the Filter type out of filtering ops; just set
    ``filter_type`` at the top of your test case, and then use
    ``assertFilterPasses`` and ``assertFilterErrors`` to check use
    cases.
    """
    filter_type = None # type: Callable[[...], BaseFilter]

    class unmodified(object):
        """
        Used by ``assertFilterPasses`` so that you can omit the
        ``expected_value`` parameter.
        """
        pass

    class skip_value_check(object):
        """
        Used by ``assertFilterPasses`` to skip checking the filtered
        value.  This is useful for tests where a simple equality
        check is not practical.

        Note:  If you use ``skip_value_check``, you should add extra
        assertions to your test to make sure the filtered value
        conforms to expectations.
        """
        pass

    def assertFilterPasses(self, runner, expected_value=unmodified):
        """
        Asserts that the FilterRunner returns the specified value,
        without errors.

        :param runner:
            Usually a FilterRunner instance, but you can pass in the
            test value itself if you want (it will automatically be run
            through ``_filter``).

        :param expected_value:
            The expected value for ``runner.cleaned_data``.

            If omitted, the assertion will check that the incoming
            value is returned unmodified.
        """
        self.assertFilterErrors(runner, {}, expected_value)

    def assertFilterErrors(self, runner, expected_codes, expected_value=None):
        """
        Asserts that the FilterRunner generates the specified error
        codes.

        :param runner:
            Usually a FilterRunner instance, but you can pass in the
            test value itself if you want (it will automatically be
            run through `_filter`).

        :param expected_value:
            Expected value for ``runner.cleaned_data`` (usually
            ``None``).
        """
        if not isinstance(runner, FilterRunner):
            runner = self._filter(runner) # type: FilterRunner

        # First check to make sure no unhandled exceptions occurred.
        if runner.has_exceptions:
            # noinspection PyTypeChecker
            self.fail(
                'Unhandled exceptions occurred while filtering the '
                'request payload:\n\n{tracebacks}\n\n'
                'Filter Messages:\n\n{messages}'.format(
                    messages = pformat(dict(runner.filter_messages)),

                    tracebacks = pformat(list(
                        starmap(format_exception, runner.exc_info)
                    )),
                )
            )

        if isinstance(expected_codes, list):
            expected_codes = {'': expected_codes}

        if runner.error_codes != expected_codes:
            # noinspection PyTypeChecker
            self.fail(
                'Filter generated unexpected error codes (expected '
                '{expected}):\n\n{messages}'.format(
                    expected    = json.dumps(sorted_dict(expected_codes)),
                    messages    = pformat(dict(runner.filter_messages)),
                ),
            )

        check_value = (
                (self.skip_value_check is not True)
            and (expected_value is not self.skip_value_check)
        )

        if check_value:
            self._check_filter_value(
                runner.cleaned_data,
                runner.data
                    if expected_value is self.unmodified
                    else expected_value
            )

    def _filter(self, *args, **kwargs):
        # type: (...) -> FilterRunner
        """
        Applies the Filter to the specified value.

        Generally, you don't have to use this method in your test case,
        unless you want to specify Filter options.

        Example::

            self.filter_type = Min

            # Min().apply(42)
            self.assertFilterPasses(42)

            # Min(min_val=40).apply(42)
            self.assertFilterPasses(self._filter(42, min_val=40))

        :param args:
            Positional params to pass to the Filter's initializer.

        :param kwargs:
            Keyword params to pass to the Filter's initializer.
        """
        if not callable(self.filter_type):
            self.fail('{cls}.filter_type is not callable.'.format(
                cls = type(self).__name__,
            ))

        if not args:
            self.fail(
                'First argument to {cls}._filter '
                'must be the filtered value.'.format(
                    cls = type(self).__name__,
                ),
            )

        return FilterRunner(
            starting_filter     = self.filter_type(*args[1:], **kwargs),
            incoming_data       = args[0],
            capture_exc_info    = True,
        )

    def _check_filter_value(self, cleaned_data, expected):
        """
        Checks the value returned by the Filter, used by
        ``assertFilterPasses``.

        In certain cases, it may be useful to override this method in
        your test case subclass.

        :param cleaned_data:
            ``cleaned_data`` from the FilterRunner.
        """
        self.assertEqual(cleaned_data, expected)
