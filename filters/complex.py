# coding=utf-8
from __future__ import absolute_import, division, print_function, \
    unicode_literals

from collections import OrderedDict
from typing import Any, Dict, Generator, Iterable, Mapping, Optional, \
    Text, Tuple, Union

from six import iteritems, iterkeys, python_2_unicode_compatible

from filters.base import BaseFilter, FilterCompatible, FilterError, Type
from filters.string import Unicode

__all__ = [
    'FilterMapper',
    'FilterRepeater',
]


@python_2_unicode_compatible
class FilterRepeater(BaseFilter):
    """
    Applies a filter to every value in an Iterable.

    You can apply a FilterRepeater to a dict (or other Mapping).  The
    filters will be applied to the Mapping's values.

    Note:  The resulting value will be coerced to a list or OrderedDict
    (depending on the input value).
    """
    CODE_EXTRA_KEY = 'unexpected'

    templates = {
        CODE_EXTRA_KEY: 'Unexpected key "{key}".',
    }

    mapping_result_type     = OrderedDict
    sequence_result_type    = list

    def __init__(self, filter_chain, restrict_keys=None):
        # type: (FilterCompatible, Optional[Iterable]) -> None
        """
        :param filter_chain:
            The filter(s) that will be applied to each item in the
            incoming iterables.

        :param restrict_keys:
            Only these keys/indexes will be allowed (any other
            keys/indexes encountered will be treated as invalid
            values).

            Important:  If this is an empty container will result in
            EVERY key/index being rejected!

            Set to ``None`` (default) to allow any key/index.
        """
        super(FilterRepeater, self).__init__()

        self._filter_chain = self.resolve_filter(filter_chain, parent=self)

        self.restrict_keys = (
            None
                if restrict_keys is None
                else set(restrict_keys)
        )

    def __str__(self):
        return '{type}({filter_chain})'.format(
            type            = type(self).__name__,
            filter_chain    = self._filter_chain,
        )

    # noinspection PyProtectedMember
    @classmethod
    def __copy__(cls, the_filter):
        # type: (FilterRepeater) -> FilterRepeater
        """
        Creates a shallow copy of the object.
        """
        new_filter = super(FilterRepeater, cls).__copy__(the_filter) # type: FilterRepeater

        new_filter._filter_chain = the_filter._filter_chain
        new_filter.restrict_keys = the_filter.restrict_keys

        return new_filter

    def _apply(self, value):
        value = self._filter(value, Type(Iterable)) # type: Iterable

        if self._has_errors:
            return None

        result_type = (
            self.mapping_result_type
                if isinstance(value, Mapping)
                else self.sequence_result_type
        )

        return result_type(self.iter(value))

    def iter(self, value):
        # type: (Iterable) -> Generator[Any]
        """
        Iterator version of :py:meth:`apply`.
        """
        if value is not None:
            if isinstance(value, Mapping):
                for k, v in iteritems(value):
                    u_key = self.unicodify_key(k)

                    if (
                            (self.restrict_keys is None)
                        or  (k in self.restrict_keys)
                    ):
                        yield k, self._apply_item(u_key, v, self._filter_chain)
                    else:
                        # For consistency with FilterMapper, invalid
                        # keys are not included in the filtered
                        # value (hence this statement does not
                        # ``yield``).
                        self._invalid_value(
                            value   = v,
                            reason  = self.CODE_EXTRA_KEY,
                            sub_key = u_key,
                        )
            else:
                for i, v in enumerate(value):
                    u_key = self.unicodify_key(i)

                    if (
                            (self.restrict_keys is None)
                        or  (i in self.restrict_keys)
                    ):
                        yield self._apply_item(u_key, v, self._filter_chain)
                    else:
                        # Unlike in mappings, it is not possible to
                        # identify a "missing" item in a collection,
                        # so we have to ensure that something ends up
                        # in the filtered value at the same position
                        # as the invalid incoming value.
                        yield self._invalid_value(
                            value   = v,
                            reason  = self.CODE_EXTRA_KEY,
                            sub_key = u_key,
                        )

    def _apply_item(self, key, value, filter_chain):
        # type: (Text, Any, FilterCompatible) -> Any
        """
        Applies filters to a single value in the iterable.

        Override this method in a subclass if you want to customize the
        way specific items get filtered.
        """
        return self._filter(value, filter_chain, sub_key=key)

    @staticmethod
    def unicodify_key(key):
        # type: (Any) -> Text
        """
        Converts a key value into a unicode so that it can be
        represented in e.g., error message contexts.
        """
        if key is None:
            return 'None'

        try:
            return Unicode().apply(key)
        except FilterError:
            return repr(key)


@python_2_unicode_compatible
class FilterMapper(BaseFilter):
    """
    Given a dict of filters, applies each filter to the corresponding
    value in incoming mappings.

    The resulting value is an OrderedDict.  The order of keys in the
    ``filter_map`` passed to the initializer determines the order of
    keys in the filtered value.

    Note: The order of extra keys is undefined, but they will always be
    last.
    """
    CODE_EXTRA_KEY      = 'unexpected'
    CODE_MISSING_KEY    = 'missing'

    templates = {
        CODE_EXTRA_KEY:     'Unexpected key "{actual_key}".',
        CODE_MISSING_KEY:   '{key} is required.',
    }

    def __init__(
            self,
            filter_map,
            allow_missing_keys  = True,
            allow_extra_keys    = True,
    ):
        # type: (Dict[Text, FilterCompatible], Union[bool, Iterable[Text]], Union[bool, Iterable[Text]]) -> None
        """
        :param filter_map:
            This mapping also determines the key order of the resulting
            OrderedDict.  If necessary, make sure that your code
            provides ``filter_map`` as an OrderedDict.

        :param allow_missing_keys:
            Determines how values with missing keys (according to
            ``filter_map``) get handled:

            - True: The missing values are set to ``None`` and then
              filtered as normal.
            - False: Missing keys are treated as invalid values.
            - <Iterable>: Only the specified keys are allowed to be
              omitted.

        :param allow_extra_keys:
            Determines how values with extra keys (according to
            ``filter_map``) get handled:

            - True: The extra values are passed through to the filtered
              value.
            - False: Extra values are treated as invalid values and
              omitted from the filtered value.
            - <Iterable>: Only the specified extra keys are allowed.
        """
        super(FilterMapper, self).__init__()

        self._filters = OrderedDict()

        self.allow_missing_keys = (
            set(allow_missing_keys)
                if isinstance(allow_missing_keys, Iterable)
                else bool(allow_missing_keys)
        )

        self.allow_extra_keys = (
            set(allow_extra_keys)
                if isinstance(allow_extra_keys, Iterable)
                else bool(allow_extra_keys)
        )

        if filter_map:
            for key, filter_chain in iteritems(filter_map): # type: Tuple[Text, BaseFilter]
                #
                # Note that the normalized Filter could be `None`.
                #
                # This has the effect of making a key "required"
                # (depending on `allow_missing_keys`) without
                # applying any Filters to the value.
                #
                self._filters[key] =\
                    self.resolve_filter(filter_chain, parent=self, key=key)

        # If the filter map is an OrderedDict, we should try to
        # preserve order when applying the filter.  Otherwise use a
        # plain ol' dict to improve readability.
        self.result_type = (
            OrderedDict
                if isinstance(filter_map, OrderedDict)
                else dict
        )


    def __str__(self):
        return '{type}({filters})'.format(
            type    = type(self).__name__,
            filters = ', '.join(
                '{key}={filter}'.format(key=key, filter=filter_chain)
                    for key, filter_chain in iteritems(self._filters)
            ),
        )

    def _apply(self, value):
        value = self._filter(value, Type(Mapping)) # type: Mapping

        if self._has_errors:
            return None

        return self.result_type(self.iter(value))

    def iter(self, value):
        # type: (Mapping) -> Generator[Text, Any]
        """
        Iterator version of :py:meth:`apply`.
        """
        if value is not None:
            # Apply filtered values first.
            for key, filter_chain in iteritems(self._filters):
                if key in value:
                    yield key, self._apply_item(key, value[key], filter_chain)

                elif self._missing_key_allowed(key):
                    # Filter the missing value as if it was set to
                    # ``None``.
                    yield key, self._apply_item(key, None, filter_chain)

                else:
                    # Treat the missing value as invalid.
                    yield key, self._invalid_value(
                        value   = None,
                        reason  = self.CODE_MISSING_KEY,
                        sub_key = key,
                    )

            # Extra values go last.
            # Note that we iterate in sorted order, in case the result
            # type preserves ordering.
            # https://github.com/eflglobal/filters/issues/13
            for key in sorted(
                            set(iterkeys(value))
                        -   set(iterkeys(self._filters))
            ):
                if self._extra_key_allowed(key):
                    yield key, value[key]
                else:
                    unicode_key = self.unicodify_key(key)

                    # Handle the extra value just like any other
                    # invalid value, but do not include it in the
                    # result (note that there is no ``yield`` here).
                    self._invalid_value(
                        value   = value[key],
                        reason  = self.CODE_EXTRA_KEY,
                        sub_key = unicode_key,

                        # https://github.com/eflglobal/filters/issues/15
                        template_vars = {
                            'actual_key': unicode_key,
                        },
                    )

    def _apply_item(self, key, value, filter_chain):
        # type: (Text, Any, FilterCompatible) -> Any
        """
        Applies filters to a single item in the mapping.

        Override this method in a subclass if you want to customize the
        way specific items get filtered.
        """
        return self._filter(value, filter_chain, sub_key=key)

    def _missing_key_allowed(self, key):
        # type: (Text) -> bool
        """
        Returns whether the specified key is allowed to be omitted from
        the incoming value.
        """
        if self.allow_missing_keys is True:
            return True

        try:
            return key in self.allow_missing_keys
        except TypeError:
            return False

    def _extra_key_allowed(self, key):
        # type: (Text) -> bool
        """
        Returns whether the specified extra key is allowed.
        """
        if self.allow_extra_keys is True:
            return True

        try:
            return key in self.allow_extra_keys
        except TypeError:
            return False

    @staticmethod
    def unicodify_key(key):
        # type: (Text) -> Text
        """
        Converts a key value into a unicode so that it can be
        represented in e.g., error message contexts.
        """
        if key is None:
            return 'None'

        try:
            return Unicode().apply(key)
        except FilterError:
            return repr(key)
