import typing

import filters as f
from filters.macros import filter_macro


class TestFilterAlpha(f.BaseFilter):
    """
    A filter that can be used for testing.
    """

    def _apply(self, value):
        return value


class TestFilterBravo(f.BaseFilter):
    """
    A filter that will can be used for testing.
    """

    def __init__(self, name: typing.Optional[str] = None) -> None:
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
