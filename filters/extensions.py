# coding=utf-8
from __future__ import absolute_import, division, print_function, \
    unicode_literals

from inspect import getmembers as get_members, isabstract as is_abstract, \
    isclass as is_class, ismodule as is_module
from logging import getLogger
from typing import Any, Dict, Generator, Text, Tuple, Type, Union

from class_registry import EntryPointClassRegistry
from pkg_resources import EntryPoint, iter_entry_points

from filters.base import BaseFilter

__all__ = [
    'FilterExtensionRegistry',
    'GROUP_NAME',
]

GROUP_NAME = 'filters.extensions'
"""
The key to use when declaring entry points in your library's
``setup.py`` file.

Example::

   setup(
     ...
     entry_points = {
       'filters.extensions': [
         # Declare each filter with its own entry point.
         'Country=filters_iso:Country',
         'Currency=filters_iso:Currency',
       ],
     },
   )

Filters that are loaded this way are accessible from
:py:data:`filters.ext` (not imported into the global namespace because
it gives IDEs a heart attack).
"""

logger = getLogger(__name__)

class FilterExtensionRegistry(EntryPointClassRegistry):
    """
    Creates a registry that can be used to dynamically load 3rd-party
    filters into the (nearly) top-level namespace.
    """
    def __init__(self, group=GROUP_NAME):
        # type: (Text) -> None
        """
        :param group:
            The name of the entry point group that will be used to load
            new classes.
        """
        super(FilterExtensionRegistry, self).__init__(group)

    def __getattr__(self, item):
        # type: (Text) -> Type[BaseFilter]
        return self[item]

    def _get_cache(self):
        # type: () -> Dict[Text, Type[BaseFilter]]
        if self._cache is None:
            self._cache = {}

            for target in iter_entry_points(self.group): # type: EntryPoint
                filter_ = target.load()

                ift_result = is_filter_type(filter_)

                if ift_result is True:
                    logger.debug(
                        'Registering extension filter '
                        '{cls.__module__}.{cls.__name__} as {name}.'.format(
                            cls     = filter_,
                            name    = target.name,
                        ),
                    )

                    self._cache[target.name] = filter_

                else:
                    logger.debug(
                        'Using legacy extension loader for '
                        '{target.name} ({reason}).'.format(
                            reason  = ift_result,
                            target  = target,
                        ),
                    )

                    self._cache.update(iter_filters_in(filter_))

        # noinspection PyTypeChecker
        return self._cache

    @staticmethod
    def create_instance(class_, *args, **kwargs):
        # type: (type, ...) -> Any
        if args or kwargs:
            return class_(*args, **kwargs)

        return class_



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
