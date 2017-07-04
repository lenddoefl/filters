# coding=utf-8
from __future__ import absolute_import, division, print_function, \
    unicode_literals

from typing import Optional, Text

import filters as f
from filters.macros import filter_macro


# noinspection PyClassHasNoInit
class TestFilterAlpha(f.BaseFilter):
    """
    A filter that can be used for testing.
    """
    def _apply(self, value):
        return value


# noinspection PyClassHasNoInit
class TestFilterBravo(f.BaseFilter):
    """
    A filter that will can be used for testing.
    """
    def __init__(self, name=None):
        # type: (Optional[Text]) -> None
        super(TestFilterBravo, self).__init__()

        self.name = name

    def _apply(self, value):
        return value


@filter_macro
def TestFilterCharlie():
    """
    A filter macro that can be used for testing.
    """
    return f.NoOp
