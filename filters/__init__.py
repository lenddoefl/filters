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

# These imports can be included in any order...
# ... so we alphabetized them (hint, hint).
from .iso import *
from .string import *


# :see: http://stackoverflow.com/a/2073599/
from pkg_resources import require
__version__ = require('filters')[0].version
del require
