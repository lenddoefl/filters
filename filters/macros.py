# coding=utf-8
from __future__ import absolute_import, unicode_literals

from functools import partial, WRAPPER_ASSIGNMENTS
from six import with_metaclass

from filters.base import BaseFilter, FilterMeta

__all__ = [
    'filter_macro',
]


def filter_macro(func, *args, **kwargs):
    """
    Promotes a function that returns a Filter into its own Filter type.

    Example::

        @filter_macro
        def String():
            return Unicode | Strip | NotEmpty

        # You can now use `String` anywhere you would use a regular Filter:
        (String | Split(':')).apply('...')

    You can also use ``filter_macro`` to create partials, allowing you to
    preset one or more initialization arguments::

        Minor = filter_macro(Max, max_value=18, inclusive=False)
        Minor.apply(42)
    """
    filter_partial = partial(func, *args, **kwargs)

    class FilterMacroMeta(FilterMeta):
        @staticmethod
        def __new__(mcs, name, bases, attrs):
            # This is as close as we can get to running
            # ``update_wrapper`` on a type.
            for attr in WRAPPER_ASSIGNMENTS:
                if hasattr(func, attr):
                    attrs[attr] = getattr(func, attr)

            # Note that we ignore the ``name`` argument, passing in
            # ``func.__name__`` instead.
            return super(FilterMacroMeta, mcs)\
                .__new__(mcs, func.__name__, bases, attrs)

        def __call__(cls, *runtime_args, **runtime_kwargs):
            return filter_partial(*runtime_args, **runtime_kwargs)

    class FilterMacro(with_metaclass(FilterMacroMeta, BaseFilter)):
        # This method will probably never get called due to overloaded
        # ``__call__`` in the metaclass, but just in case, we'll include
        # it because it is an abstract method in `BaseFilter`.
        def _apply(self, value):
            # noinspection PyProtectedMember
            return self.__class__()._apply(value)

    return FilterMacro
