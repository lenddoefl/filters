import typing
from collections import OrderedDict

from filters.base import BaseFilter, FilterCompatible, FilterError, Type
from filters.simple import Choice, Length
from filters.string import Unicode

__all__ = [
    'FilterMapper',
    'FilterRepeater',
    'FilterSwitch',
    'NamedTuple',
]


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

    mapping_result_type = OrderedDict
    sequence_result_type = list

    def __init__(
            self,
            filter_chain: FilterCompatible,
            restrict_keys: typing.Optional[typing.Iterable] = None,
    ) -> None:
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
        super().__init__()

        self._filter_chain = self.resolve_filter(filter_chain, parent=self)

        self.restrict_keys = (
            None
            if restrict_keys is None
            else set(restrict_keys)
        )

    def __str__(self):
        return '{type}({filter_chain})'.format(
            type=type(self).__name__,
            filter_chain=self._filter_chain,
        )

    @classmethod
    def __copy__(cls, the_filter: 'FilterRepeater') -> 'FilterRepeater':
        """
        Creates a shallow copy of the object.
        """
        new_filter = super().__copy__(the_filter)

        new_filter._filter_chain = the_filter._filter_chain
        new_filter.restrict_keys = the_filter.restrict_keys

        # noinspection PyTypeChecker
        return new_filter

    def _apply(self, value):
        value = self._filter(
            value,
            Type(typing.Iterable),
        )  # type: typing.Iterable

        if self._has_errors:
            return None

        result_type = (
            self.mapping_result_type
            if isinstance(value, typing.Mapping)
            else self.sequence_result_type
        )

        return result_type(self.iter(value))

    def iter(self, value: typing.Iterable) -> typing.Generator[
        typing.Any, None, None]:
        """
        Iterator version of :py:meth:`apply`.
        """
        if value is not None:
            if isinstance(value, typing.Mapping):
                for k, v in value.items():
                    u_key = self.unicodify_key(k)

                    if (
                            (self.restrict_keys is None)
                            or (k in self.restrict_keys)
                    ):
                        yield k, self._apply_item(u_key, v, self._filter_chain)
                    else:
                        # For consistency with FilterMapper, invalid
                        # keys are not included in the filtered
                        # value (hence this statement does not
                        # ``yield``).
                        self._invalid_value(
                            value=v,
                            reason=self.CODE_EXTRA_KEY,
                            sub_key=u_key,
                        )
            else:
                for i, v in enumerate(value):
                    u_key = self.unicodify_key(i)

                    if (
                            (self.restrict_keys is None)
                            or (i in self.restrict_keys)
                    ):
                        yield self._apply_item(u_key, v, self._filter_chain)
                    else:
                        # Unlike in mappings, it is not possible to
                        # identify a "missing" item in a collection,
                        # so we have to ensure that something ends up
                        # in the filtered value at the same position
                        # as the invalid incoming value.
                        yield self._invalid_value(
                            value=v,
                            reason=self.CODE_EXTRA_KEY,
                            sub_key=u_key,
                        )

    def _apply_item(
            self,
            key: str,
            value: typing.Any,
            filter_chain: FilterCompatible,
    ) -> typing.Any:
        """
        Applies filters to a single value in the iterable.

        Override this method in a subclass if you want to customize the
        way specific items get filtered.
        """
        return self._filter(value, filter_chain, sub_key=key)

    @staticmethod
    def unicodify_key(key: typing.Any) -> str:
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
    CODE_EXTRA_KEY = 'unexpected'
    CODE_MISSING_KEY = 'missing'

    templates = {
        CODE_EXTRA_KEY:   'Unexpected key "{actual_key}".',
        CODE_MISSING_KEY: '{key} is required.',
    }

    def __init__(
            self,
            filter_map: typing.Mapping[str, FilterCompatible],
            allow_missing_keys: typing.Union[
                bool, typing.Iterable[str]] = True,
            allow_extra_keys: typing.Union[bool, typing.Iterable[str]] = True,
    ) -> None:
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
        super().__init__()

        self._filters = OrderedDict()

        self.allow_missing_keys = (
            set(allow_missing_keys)
            if isinstance(allow_missing_keys, typing.Iterable)
            else bool(allow_missing_keys)
        )

        self.allow_extra_keys = (
            set(allow_extra_keys)
            if isinstance(allow_extra_keys, typing.Iterable)
            else bool(allow_extra_keys)
        )

        if filter_map:
            for key, filter_chain in filter_map.items():
                #
                # Note that the normalized Filter could be `None`.
                #
                # This has the effect of making a key "required"
                # (depending on `allow_missing_keys`) without
                # applying any Filters to the value.
                #
                self._filters[key] = self.resolve_filter(
                    filter_chain,
                    parent=self,
                    key=key,
                )

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
            type=type(self).__name__,
            filters=', '.join(
                '{key}={filter}'.format(key=key, filter=filter_chain)
                    for key, filter_chain in self._filters.items()
            ),
        )

    def _apply(self, value):
        value = self._filter(
            value,
            Type(typing.Mapping),
        )  # type: typing.Mapping

        if self._has_errors:
            return None

        return self.result_type(self.iter(value))

    def iter(self, value: typing.Mapping) -> typing.Generator[
        typing.Tuple[str, typing.Any], None, None]:
        """
        Iterator version of :py:meth:`apply`.
        """
        if value is not None:
            # Apply filtered values first.
            for key, filter_chain in self._filters.items():
                if key in value:
                    yield key, self._apply_item(key, value[key], filter_chain)

                elif self._missing_key_allowed(key):
                    # Filter the missing value as if it was set to
                    # ``None``.
                    yield key, self._apply_item(key, None, filter_chain)

                else:
                    # Treat the missing value as invalid.
                    yield key, self._invalid_value(
                        value=None,
                        reason=self.CODE_MISSING_KEY,
                        sub_key=key,
                    )

            # Extra values go last.
            # Note that we iterate in sorted order, in case the result
            # type preserves ordering.
            # https://github.com/eflglobal/filters/issues/13
            for key in sorted(
                    set(value.keys())
                    - set(self._filters.keys())
            ):
                if self._extra_key_allowed(key):
                    yield key, value[key]
                else:
                    unicode_key = self.unicodify_key(key)

                    # Handle the extra value just like any other
                    # invalid value, but do not include it in the
                    # result (note that there is no ``yield`` here).
                    self._invalid_value(
                        value=value[key],
                        reason=self.CODE_EXTRA_KEY,
                        sub_key=unicode_key,

                        # https://github.com/eflglobal/filters/issues/15
                        template_vars={
                            'actual_key': unicode_key,
                        },
                    )

    def _apply_item(
            self,
            key: str,
            value: typing.Any,
            filter_chain: FilterCompatible,
    ) -> typing.Any:
        """
        Applies filters to a single item in the mapping.

        Override this method in a subclass if you want to customize the
        way specific items get filtered.
        """
        return self._filter(value, filter_chain, sub_key=key)

    def _missing_key_allowed(self, key: str) -> bool:
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

    def _extra_key_allowed(self, key: str) -> bool:
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
    def unicodify_key(key: typing.Any) -> str:
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


class FilterSwitch(BaseFilter):
    """
    Chooses the next filter to apply based on the output of a callable.
    """

    def __init__(
            self,
            getter: typing.Callable[[typing.Any], typing.Hashable],
            cases: typing.Mapping[typing.Hashable, FilterCompatible],
            default: typing.Optional[FilterCompatible] = None,
    ) -> None:
        """
        :param getter:
            Callable used to extract the value to match against switch
            cases.

        :param cases:
            Mapping of possible values to the corresponding filters.

        :param default:
            Default filter to use, if none of the cases are matched.

            If null (default) then the value will be considered invalid
            if it doesn't match any cases.
        """
        super().__init__()

        self.getter = getter
        self.cases = cases
        self.default = default

    def _apply(self, value):
        gotten = self.getter(value)  # type: typing.Hashable

        if not self.default:
            gotten = self._filter(gotten, Choice(self.cases.keys()))

            if self._has_errors:
                return None

        if gotten in self.cases:
            return self._filter(value, self.cases[gotten])

        # If we get here, then we have set a default filter.
        return self._filter(value, self.default)



class NamedTuple(BaseFilter):
    """
    Attempts to convert the incoming value into a namedtuple.
    """

    def __init__(
            self,
            type_: typing.Type[typing.NamedTuple],
            filter_map: typing.Optional[
                typing.Mapping[str, FilterCompatible]] = None,
    ) -> None:
        """
        :param type_:
            The type of namedtuple into which the filter will attempt to
            convert incoming values.

        :param filter_map:
            Specifies additional filters that should be applied to each
            attribute in the resulting namedtuple object.

            For example::

                >>> import filters as f
                >>> from collections import namedtuple
                >>> Color = namedtuple('Color', ('r', 'g', 'b'))

                >>> # noinspection PyTypeChecker
                >>> filter_chain = f.NamedTuple(Color, {
                ...     'r': f.Required | f.Int | f.Min(0) | f.Max(255),
                ...     'g': f.Required | f.Int | f.Min(0) | f.Max(255),
                ...     'b': f.Required | f.Int | f.Min(0) | f.Max(255),
                ... })

                >>> filter_chain.apply(['64', '128', '192'])
                Color(r=64, g=128, b=192)
        """
        super().__init__()

        self.type = type_

        if filter_map:
            self.filter_mapper = FilterMapper(filter_map)
        else:
            self.filter_mapper = None

    def _apply(self, value):
        value = self._filter(value, Type((typing.Iterable, typing.Mapping)))

        if self._has_errors:
            return None

        if not isinstance(value, self.type):
            if isinstance(value, typing.Mapping):
                # Check that the incoming value has exactly the right
                # keys.
                # noinspection PyProtectedMember
                value = self._filter(value, FilterMapper(
                    dict.fromkeys(self.type._fields),
                    allow_extra_keys=False,
                    allow_missing_keys=False,
                ))

                if self._has_errors:
                    return None

                value = self.type(**value)
            else:
                # Check that the incoming value has exactly the right
                # number of values.
                # noinspection PyProtectedMember
                value = self._filter(value, Length(len(self.type._fields)))

                if self._has_errors:
                    return None

                value = self.type(*value)

        # At this point, ``value`` is an instance of :py:attr:`type`.
        # Now we just need to figure out whether additional filtering is
        # necessary.
        if self.filter_mapper:
            # noinspection PyProtectedMember
            filtered = self._filter(value._asdict(), self.filter_mapper)

            if self._has_errors:
                return None

            return self.type(**filtered)
        else:
            return value
