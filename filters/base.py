from abc import ABCMeta, abstractmethod as abstract_method
from copy import copy
from typing import Any, Callable, Iterable, List, Mapping, \
    MutableMapping, Optional as OptionalType, Tuple, Union
from weakref import ProxyTypes, proxy

__all__ = [
    'BaseFilter',
    'BaseInvalidValueHandler',
    'ExceptionHandler',
    'FilterChain',
    'FilterCompatible',
    'FilterError',
    'FilterMeta',
    'Type',
]

FilterCompatible = \
    OptionalType[Union['BaseFilter', 'FilterMeta', Callable[[], 'BaseFilter']]]
"""
Used in PEP-484 type hints to indicate a value that can be normalized
into an instance of a :py:class:`filters.base.BaseFilter` subclass.
"""


class FilterMeta(ABCMeta):
    """
    Metaclass for filters.
    """

    # noinspection PyShadowingBuiltins
    def __init__(cls, what, bases=None, dict=None, **kwargs):
        # noinspection PyArgumentList
        super().__init__(what, bases, dict, **kwargs)

        if not hasattr(cls, 'templates'):
            cls.templates = {}

        # Copy error templates from base class to derived class, but
        # in the event of a conflict, preserve the derived class'
        # template.
        templates = {}
        for base in bases:
            if isinstance(base, FilterMeta):
                templates.update(base.templates)

        if templates:
            templates.update(cls.templates)
            cls.templates = templates

    def __or__(self, next_filter: FilterCompatible) -> 'FilterChain':
        """
        Convenience alias for adding a Filter with default
        configuration to a FilterChain.

        E.g., the following statements do the same thing::

            Int | Max(32)   # FilterMeta.__or__
            Int() | Max(32) # Filter.__or__

        References:
          - http://stackoverflow.com/a/10773232
        """
        return FilterChain(self) | next_filter


class BaseFilter(metaclass=FilterMeta):
    """
    Base functionality for all Filters, macros, etc.
    """
    CODE_EXCEPTION = 'exception'

    templates = {
        CODE_EXCEPTION: 'An error occurred while processing this value.',
    }

    def __init__(self):
        super().__init__()

        self._parent = None  # type: OptionalType[BaseFilter]
        self._handler = None  # type: OptionalType[BaseInvalidValueHandler]
        self._key = None  # type: OptionalType[str]

        #
        # Indicates whether the Filter detected any invalid values.
        # It gets reset every time `apply` gets called.
        #
        # Note that this attribute is intended to be used internally;
        # external code should instead interact with invalid value
        # handlers such as LogHandler and MemoryHandler.
        #
        # References:
        #   - :py:mod:`importer.core.filters.handlers`
        #
        self._has_errors = False

    # noinspection PyProtectedMember
    @classmethod
    def __copy__(cls, the_filter: 'BaseFilter') -> 'BaseFilter':
        """
        Creates a shallow copy of the object.
        """
        new_filter = type(the_filter)()  # type: BaseFilter

        new_filter._parent = the_filter._parent
        new_filter._key = the_filter._key
        new_filter._handler = the_filter._handler

        return new_filter

    def __or__(self, next_filter: FilterCompatible) -> 'FilterChain':
        """
        Chains another filter with this one.
        """
        normalized = self.resolve_filter(next_filter)

        if normalized:
            #
            # Officially, we should do this:
            # return ``FilterChain(self) | next_filter``
            #
            # But that wastes some CPU cycles by creating an extra
            # FilterChain instance that gets thrown away almost
            # immediately. It's a bit faster just to create a single
            # FilterChain instance and modify it in-place.
            #
            # noinspection PyProtectedMember
            return FilterChain(self)._add(next_filter)
        else:
            return self if isinstance(self, FilterChain) else FilterChain(self)

    def __str__(self):
        """
        Returns a string representation of the Filter.

        Note that the output of this method does not necessarily match
        the signature of the Filter's ``__init__`` method; rather,
        its purpose is to provide a snapshot of critical parts of
        the Filter's configuration for e.g., troubleshooting
        purposes.
        """
        return '{type}()'.format(
            type=type(self).__name__,
        )

    @property
    def parent(self) -> OptionalType['BaseFilter']:
        """
        Returns the parent Filter.
        """
        # Make sure `self._parent` hasn't gone away.
        try:
            # noinspection PyStatementEffect
            self._parent.__class__
        except ReferenceError:
            return None

        return self._parent

    @parent.setter
    def parent(self, parent: 'BaseFilter') -> None:
        """
        Sets the parent Filter.
        """
        # Create a weakref to the parent Filter to prevent annoying the
        # garbage collector.
        self._parent = (
            (parent if isinstance(parent, ProxyTypes) else proxy(parent))
            if parent
            else None
        )

    @property
    def key(self) -> str:
        """
        Returns the key associated with this filter.
        """
        return self._make_key(self._key_parts)

    @key.setter
    def key(self, key: str) -> None:
        """
        Sets the key associated with this filter.
        """
        self._key = key

    def sub_key(self, sub_key: str) -> str:
        """
        Returns a copy of this filter's key with an additional sub-key
        appended.
        """
        return self._make_key(self._key_parts + [sub_key])

    @property
    def _key_parts(self) -> List[str]:
        """
        Assembles each key part in the filter hierarchy.
        """
        key_parts = []

        # Iterate up the parent chain and collect key parts.
        # Alternatively, we could just get ``self.parent._key_parts``,
        # but that is way less efficient.
        parent = self
        while parent:
            # As we move up the chain, push key parts onto the front of
            # the path (otherwise the key parts would be in reverse
            # order).
            key_parts.insert(0, parent._key)
            parent = parent.parent

        return key_parts

    @property
    def handler(self) -> 'BaseInvalidValueHandler':
        """
        Returns the invalid value handler for the filter.
        """
        if self._handler is None:
            # Attempt to return the parent filter's handler...
            try:
                return self.parent.handler
            except AttributeError:
                #
                # ... unless this filter has no parent, in which case
                # it should use the default.
                #
                # Note that we do not set ``self._handler``, in case
                # the filter later gets added to e.g., a FilterChain
                # that has a different invalid value handler set.
                #
                return ExceptionHandler()

        return self._handler

    @handler.setter
    def handler(self, handler: 'BaseInvalidValueHandler') -> None:
        """
        Sets the invalid value handler for the filter.
        """
        self._handler = handler

    def set_handler(self, handler: 'BaseInvalidValueHandler') -> 'BaseFilter':
        """
        Cascading method for setting the filter's invalid value
        handler.
        """
        self.handler = handler
        return self

    def apply(self, value):
        """
        Applies the filter to a value.
        """
        self._has_errors = False

        try:
            return self._apply_none() if value is None else self._apply(value)
        except Exception as e:
            return self._invalid_value(value, e, exc_info=True)

    @abstract_method
    def _apply(self, value):
        """
        Applies filter-specific logic to a value.

        Note:  It is safe to assume that ``value`` is not ``None`` when
        this method is invoked.
        """
        raise NotImplementedError(
            'Not implemented in {cls}.'.format(cls=type(self).__name__),
        )

    def _apply_none(self):
        """
        Applies filter-specific logic when the value is ``None``.
        """
        return None

    def _filter(
            self,
            value: Any,
            filter_chain: FilterCompatible,
            sub_key: OptionalType[str] = None,
    ) -> Any:
        """
        Applies another filter to a value in the same context as the
        current filter.

        :param sub_key:
            Appended to the ``key`` value in the error message context
            (used by complex filters).
        """
        filter_chain = self.resolve_filter(
            filter_chain,
            parent=self,
            key=sub_key,
        )

        # In rare cases, ``filter_chain`` may be ``None``.
        # :py:meth:`filters.complex.FilterMapper.__init__`
        if filter_chain:
            try:
                filtered = filter_chain.apply(value)
            except Exception as e:
                return self._invalid_value(value, e, exc_info=True)
            else:
                # noinspection PyProtectedMember
                self._has_errors = self._has_errors or filter_chain._has_errors
                return filtered
        else:
            return value

    def _invalid_value(
            self,
            value: Any,
            reason: Union[str, Exception],
            replacement: OptionalType[Any] = None,
            exc_info: bool = False,
            context: OptionalType[MutableMapping] = None,
            sub_key: OptionalType[str] = None,
            template_vars: OptionalType[Mapping] = None,
    ) -> Any:
        """
        Handles an invalid value.

        This method works as both a logging method and an exception
        handler.

        :param replacement:
            The replacement value to use instead.

        :param sub_key:
            Appended to the ``key`` value in the error message context
            (used by complex filters).

        :return:
            Replacement value to use instead of the invalid value
            (usually ``None``).
        """
        handler = self.handler

        if isinstance(reason, FilterError):
            # FilterErrors should be sent directly to the handler.
            # This allows complex Filters to properly catch and handle
            # FilterErrors raised by the Filters they control.
            return handler.handle_invalid_value(
                message=str(reason),
                exc_info=True,
                context=getattr(reason, 'context', {}),
            )

        self._has_errors = True

        if not context:
            context = {}

        context['value'] = value
        context['filter'] = str(self)
        context['key'] = self.sub_key(sub_key)
        context['replacement'] = replacement

        if not template_vars:
            template_vars = {}

        template_vars.update(context)

        if isinstance(reason, Exception):
            # Store the error code in the context so that the caller
            # can identify the error type without having to parse the
            # rendered error message template.
            context['code'] = self.CODE_EXCEPTION

            # Store exception details in the context so that they are
            # accessible to devs but hidden from end users.
            # Note that the traceback gets processed separately,
            context['exc'] = '[{mod}.{cls}] {msg}'.format(
                mod=type(reason).__module__,
                cls=type(reason).__name__,
                msg=str(reason),
            )

            # Add the context to the exception object so that loggers
            # can use it.
            if not hasattr(reason, 'context'):
                reason.context = {}
            reason.context.update(context)

            handler.handle_exception(
                message=self._format_message(context['code'], template_vars),
                exc=reason,
            )
        else:
            # Store the error code in the context so that the caller
            # can identify the error type without having to parse the
            # rendered error message template.
            context['code'] = reason

            handler.handle_invalid_value(
                message=self._format_message(reason, template_vars),
                exc_info=exc_info,
                context=context,
            )

        return replacement

    def _format_message(
            self,
            key: str,
            template_vars: Mapping[str, str],
    ) -> str:
        """
        Formats a message for the invalid value handler.
        """
        return self.templates[key].format(**template_vars)

    @classmethod
    def resolve_filter(
            cls,
            the_filter: FilterCompatible,
            parent: OptionalType['BaseFilter'] = None,
            key: OptionalType[str] = None,
    ) -> OptionalType['FilterChain']:
        """
        Converts a filter-compatible value into a consistent type.
        """
        if the_filter is not None:
            if isinstance(the_filter, BaseFilter):
                resolved = the_filter

            elif callable(the_filter):
                resolved = cls.resolve_filter(the_filter())

            # Uhh... hm.
            else:
                raise TypeError(
                    '{type} {value!r} is not '
                    'compatible with {target}.'.format(
                        type=type(the_filter).__name__,
                        value=the_filter,
                        target=cls.__name__,
                    ),
                )

            if parent:
                resolved.parent = parent

            if key:
                resolved.key = key

            return resolved

    @staticmethod
    def _make_key(key_parts: Iterable[str]) -> str:
        """
        Assembles a dotted key value from its component parts.
        """
        return '.'.join(filter(None, key_parts))


class FilterChain(BaseFilter):
    """
    Allows you to chain multiple filters together so that they are
    treated as a single filter.
    """

    def __init__(self, start_filter: FilterCompatible = None) -> None:
        super().__init__()

        self._filters = []  # type: List[BaseFilter]

        self._add(start_filter)

    def __str__(self):
        return '{type}({filters})'.format(
            type=type(self).__name__,
            filters=' | '.join(map(str, self._filters)),
        )

    def __or__(self, next_filter: FilterCompatible) -> 'FilterChain':
        """
        Chains a filter with this one.

        This method creates a new FilterChain object without modifying
        the current one.
        """
        resolved = self.resolve_filter(next_filter)

        if resolved:
            new_chain = copy(self)  # type: FilterChain
            new_chain._add(next_filter)
            return new_chain
        else:
            return self

    @classmethod
    def __copy__(cls, the_filter: 'FilterChain') -> 'FilterChain':
        """
        Creates a shallow copy of the object.
        """
        new_filter = super().__copy__(the_filter)
        new_filter._filters = the_filter._filters[:]
        # noinspection PyTypeChecker
        return new_filter

    def _add(self, next_filter: FilterCompatible) -> 'FilterChain':
        """
        Adds a Filter to the collection directly.
        """
        resolved = self.resolve_filter(next_filter, parent=self)
        if resolved:
            self._filters.append(resolved)

        return self

    def _apply(self, value):
        for f in self._filters:
            value = self._filter(value, f)

            # FilterChains stop at the first sign of trouble.
            # This is important because FilterChains have to behave
            # consistently regardless of whether the invalid value
            # handler raises an exception.
            if self._has_errors:
                break

        return value

    def _apply_none(self):
        return self._apply(None)


class BaseInvalidValueHandler(metaclass=ABCMeta):
    """
    Base functionality for classes that handle invalid values.
    """

    @abstract_method
    def handle_invalid_value(
            self,
            message: str,
            exc_info: bool,
            context: MutableMapping,
    ) -> Any:
        """
        Handles an invalid value.

        :param message:
            Error message.

        :param exc_info:
            Whether to include output from :py:func:``sys.exc_info``.

        :param context:
            Additional context values for the error.
        """
        raise NotImplementedError(
            'Not implemented in {cls}.'.format(cls=type(self).__name__),
        )

    def handle_exception(self, message: str, exc: Exception) -> Any:
        """
        Handles an uncaught exception.
        """
        return self.handle_invalid_value(
            message=message,
            exc_info=True,
            context=getattr(exc, 'context', {}),
        )


class FilterError(ValueError):
    """
    Indicates that a parsed value could not be filtered because the
    value was invalid.
    """

    def __init__(self, *args, **kwargs):
        """
        Provides a container to include additional variables and other
        information to help troubleshoot errors.
        """
        # Exception kwargs are deprecated in Python 3, but keeping them
        # around for compatibility with Python 2.
        # noinspection PyArgumentList
        super().__init__(*args, **kwargs)
        self.context = {}


class ExceptionHandler(BaseInvalidValueHandler):
    """
    Invalid value handler that raises an exception.
    """

    def handle_invalid_value(
            self,
            message: str,
            exc_info: bool,
            context: MutableMapping,
    ) -> None:
        error = FilterError(message)
        error.context = context
        raise error


# This filter is used extensively by other filters.
# To avoid lots of needless "circular import" hacks, we'll put it in
# the base module.
class Type(BaseFilter):
    """
    Checks the type of a value.
    """
    CODE_WRONG_TYPE = 'wrong_type'

    templates = {
        CODE_WRONG_TYPE:
            '{incoming} is not valid (allowed types: {allowed}).',
    }

    def __init__(
            self,
            allowed_types: Union[type, Tuple[type, ...]],
            allow_subclass: bool = True,
            aliases: OptionalType[Mapping[type, str]] = None,
    ) -> None:
        """
        :param allowed_types:
            The type (or types) that incoming values are allowed to
            have.

        :param allow_subclass:
            Whether to allow subclasses when checking for type matches.

        :param aliases:
            Aliases to use for type names in error messages.

            This is useful for providing more context- appropriate
            names to end users and/or masking native Python type names.
        """
        super().__init__()

        # A pinch of syntactic sugar.
        self.allowed_types = (
            allowed_types
            if isinstance(allowed_types, tuple)
            else (allowed_types,)
        )
        self.allow_subclass = allow_subclass

        self.aliases = aliases or {}

    def __str__(self):
        return (
            '{type}({allowed_types}, '
            'allow_subclass={allow_subclass!r})'.format(
                type=type(self).__name__,
                allowed_types=self.get_allowed_type_names(aliased=False),
                allow_subclass=self.allow_subclass,
            )
        )

    def _apply(self, value):
        valid = (
            isinstance(value, self.allowed_types)
            if self.allow_subclass
            else (type(value) in self.allowed_types)
        )

        if not valid:
            return self._invalid_value(
                value=value,
                reason=self.CODE_WRONG_TYPE,

                template_vars={
                    'incoming': self.get_type_name(type(value)),
                    'allowed':  self.get_allowed_type_names(),
                },
            )

        return value

    def get_allowed_type_names(self, aliased: bool = True) -> str:
        """
        Returns a string with all the allowed types.
        """
        # Note that we cast as a set in the middle, to ferret out
        # duplicates.
        return ', '.join(sorted({
            self.get_type_name(t, aliased)
            for t in self.allowed_types
        }))

    def get_type_name(self, type_: type, aliased: bool = True) -> str:
        """
        Returns the name of the specified type.
        """
        # Depending on the type, it may require a bit of creativity to
        # find the proper name.
        # https://bugs.python.org/issue34422
        possible_names = [
            getattr(type_, '_name', None),
            getattr(type_, '__name__', None),
            str(type_),
        ]

        if aliased:
            possible_names.insert(0, self.aliases.get(type_))

        return next(filter(None, possible_names))
