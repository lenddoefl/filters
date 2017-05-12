# coding=utf-8
from __future__ import absolute_import, division, print_function, \
    unicode_literals

from typing import Union, Type, Callable

FilterCompatible =\
    Union['BaseFilter', Type['BaseFilter'], Callable[[], 'BaseFilter'], None]
"""
Used in PEP-484 type hints to indicate a value that can be normalized
into an instance of a :py:class:`filters.base.BaseFilter` subclass.
"""
