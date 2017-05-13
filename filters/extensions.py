# coding=utf-8
from __future__ import absolute_import, division, print_function, \
    unicode_literals

from inspect import getmembers as get_members, isabstract as is_abstract, \
    isclass as is_class, ismodule as is_module
from logging import getLogger
from typing import Any, Dict, Generator, Optional, Text, Tuple, Type, Union

from pkg_resources import EntryPoint, iter_entry_points
from six import iterkeys, python_2_unicode_compatible, text_type

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

logger = getLogger(__name__)

@python_2_unicode_compatible
class FilterExtensionRegistry(object):
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
        super(FilterExtensionRegistry, self).__init__()

        self._filters = filters

    def __dir__(self):
        self.__autoload()
        return list(iterkeys(self._filters))

    def __getattr__(self, item):
        return self[item]

    def __getitem__(self, item):
        self.__autoload()
        return self._filters.get(item)

    def __iter__(self):
        self.__autoload()
        return iter(self._filters)

    def __missing__(self, key):
        raise KeyError('Extension filter "{key}" not found!'.format(key=key))

    def __repr__(self):
        self.__autoload()
        return repr(self._filters)

    def __str__(self):
        self.__autoload()
        return text_type(self._filters)

    def __autoload(self):
        """
        Automatically loads registered extension filters, if necessary.
        """
        if self._filters is None:
            self._filters = discover_filters()


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
        logger.debug(
            'Looking for extension filters in {name} (`{target}`).'.format(
                name    = entry_point.name,
                target  = entry_point.module_name,
            ),
        )

        filters.update(iter_filters_in(entry_point.resolve()))

    return filters


def is_filter_type(target):
    # type: (Any) -> Union[bool, Text]
    """
    Returns whether the specified object can be registered as a filter.

    :return:
        Returns ``True`` if the object is a filter.
        Otherwise, returns a string indicating why it is not valid.
    """
    if not is_class(target):
        return 'not a class'

    if not issubclass(target, BaseFilter):
        return 'does not extend BaseFilter'

    if is_abstract(target):
        return 'abstract class'

    return True


def iter_filters_in(target):
    # type: (Any) -> Generator[Tuple[Text, Type[BaseFilter]]]
    """
    Iterates over all filters in the specified module/class.
    """
    ift_result = is_filter_type(target)

    if ift_result is True:
        logger.debug(
            'Registering extension filter '
            '{cls.__module__}.{cls.__name__}.'.format(
                cls = target,
            ),
        )

        yield target.__name__, target
    elif is_module(target):
        for member_name, member in get_members(target):
            member_ift_result = is_filter_type(member)

            if member_ift_result is True:
                logger.debug(
                    'Registering extension filter '
                    '{cls.__module__}.{cls.__name__}.'.format(
                        cls = member,
                    ),
                )

                yield member.__name__, member
            else:
                logger.debug(
                    'Ignoring {module}.{name} ({reason})'.format(
                        module  = target.__name__,
                        name    = member_name,
                        reason  = member_ift_result,
                    ),
                )
    elif is_class(target):
        logger.debug(
            'Ignoring {cls.__module__}.{cls.__name__} ({reason}).'.format(
                cls     = target,
                reason  = ift_result,
            ),
        )
    else:
        logger.debug(
            'Ignoring {target!r} ({reason}).'.format(
                reason  = ift_result,
                target  = target,
            ),
        )
