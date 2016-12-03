# coding=utf-8
from __future__ import absolute_import, division, print_function, \
    unicode_literals

from typing import Union, Callable

FilterCompatible =\
    Union['BaseFilter', 'FilterMeta', Callable[[], 'BaseFilter'], None]

# Make some imports accessible from the top level of the package.
# Note that the order is important here, due to dependencies.
from .base import *
from .handlers import *
from .number import *
from .simple import *
from .complex import *
from .string import *


# Don't forget to update version number in setup.py!
__version__ = '1.0.0'
