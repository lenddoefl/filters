from collections import OrderedDict
from typing import Mapping, Sequence

__all__ = [
    'JSON_ALIASES',
]

# Used by e.g. :py:class:`Type` and :py:class:`Array` to mask
# python-specific names in error messages.
JSON_ALIASES = {
    # Builtins
    bool: 'Boolean',
    bytes: 'String',
    dict: 'Object',
    float: 'Number',
    int: 'Number',
    list: 'Array',
    str: 'String',

    # Collections
    OrderedDict: 'Object',

    # Typing
    Mapping: 'Object',
    Sequence: 'Array',
}
