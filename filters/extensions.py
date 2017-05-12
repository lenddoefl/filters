# coding=utf-8
from __future__ import absolute_import, division, print_function, \
    unicode_literals

from inspect import getmembers as get_members, isabstract as is_abstract, \
    isclass as is_class, ismodule as is_module
from typing import Any, Dict, Generator, Optional, Text, Tuple, Type

from pkg_resources import EntryPoint, iter_entry_points

from filters.base import BaseFilter

ENTRY_POINT_KEY = 'filters.extensions'
"""
The key to use when declaring entry points in your library's
``setup.py`` file.

Example::

   setup(
     ...
     entry_points = {
       'filters.extensions': [
         # Load all filters from a single module.
         'iso = filters_iso',

         # Load a single class.
         'currency = filters_iso:Currency',
       ],
     },
   )

Filters that are loaded this way are accessible from
:py:data:`filters.ext` (not imported into the global namespace because
it gives IDEs a heart attack).
"""

class FilterExtensionRegistry(dict):
    """
    Creates a registry that can be used to dynamically load 3rd-party
    filters into the (nearly) top-level namespace.
    """
    def __init__(self, filters=None):
        # type: (Optional[Dict[Text, Type[BaseFilter]]]) -> None
        """
        :param filters:
            Used to preload the registry.

            If ``None``, filters will be automatically loaded from
            3rd-party libraries.

            If you want to initialize a completely empty registry,
            set ``filters`` to an empty dict.
        """
        if filters is None:
            filters = discover_filters()

        super(FilterExtensionRegistry, self).__init__(filters)

    def __getattr__(self, item):
        return self[item]


def discover_filters():
    # type: () -> Dict[Text, Type[BaseFilter]]
    """
    Returns all registered filters, in no particular order.

    If two filters have the same name, the one that gets loaded second
    will replace the first one.  Note that the order that filters are
    loaded is not defined.
    """
    filters = {} # type: Dict[Text, Type[BaseFilter]]

    for entry_point in iter_entry_points(ENTRY_POINT_KEY): # type: EntryPoint
        filters.update(iter_filters_in(entry_point.load()))

    return filters


def is_filter_type(target):
    # type: (Any) -> bool
    """
    Returns whether the specified object can be registered as a filter.
    """
    return (
            is_class(target)
        and issubclass(target, BaseFilter)
        and not is_abstract(target)
    )


def iter_filters_in(target):
    # type: (Any) -> Generator[Tuple[Text, Type[BaseFilter]]]
    """
    Iterates over all filters in the specified module/class.
    """
    if is_filter_type(target):
            yield target.__name__, target
    elif is_module(target):
        for _, member in get_members(target):
            if is_filter_type(member):
                yield member.__name__, member
