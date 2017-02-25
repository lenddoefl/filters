# coding=utf-8
from __future__ import absolute_import, division, print_function, \
    unicode_literals

from six import string_types

from filters.base import BaseFilter, Type


__all__ = [
    'Country',
    'Currency',
    'Locale',
]


class Country(BaseFilter):
    """
    Interprets an incoming value as an ISO 3166-1 alpha-2 or alpha-3
    country code.

    The resulting value is a :py:class:`iso3166.Country` object.
    """
    CODE_INVALID = 'not_iso_3166_1'

    templates = {
        CODE_INVALID: 'This is not a valid ISO 3166-1 country code.',
    }

    def _apply(self, value):
        # Lazy-load dependencies to reduce memory usage when this
        # filter is not used in a project.
        from iso3166 import (
            countries_by_alpha2,
            countries_by_alpha3,
            Country as CountryType,
        )

        value = self._filter(value, Type(string_types + (CountryType,)))

        if self._has_errors:
            return None

        if isinstance(value, CountryType):
            return value

        search_functions = {
            2: countries_by_alpha2,
            3: countries_by_alpha3,
        }

        try:
            return search_functions[len(value)][value.upper()]
        except KeyError:
            return self._invalid_value(value, self.CODE_INVALID, exc_info=True)


class Currency(BaseFilter):
    """
    Interprets an incoming value as an ISO 4217 currency code.

    The resulting value is a :py:class:`moneyed.Currency` object.
    """
    CODE_INVALID = 'not_iso_4217'

    templates = {
        CODE_INVALID: 'This is not a valid ISO 4217 currency code.',
    }

    def _apply(self, value):
        # Lazy-load dependencies to reduce memory usage when this
        # filter is not used in a project.
        from moneyed import (
            Currency as CurrencyType,
            CurrencyDoesNotExist,
            get_currency,
        )

        value = self._filter(value, Type(string_types + (CurrencyType,)))

        if self._has_errors:
            return None

        if isinstance(value, CurrencyType):
            return value

        try:
            #
            # Note that ``get_currency`` explicitly casts the incoming
            # code to ASCII, so it is possible to get a
            # UnicodeDecodeError here (e.g., the incoming value is
            # a currency symbol instead of an ISO currency code).
            #
            # To keep things simple for the end user, we will treat
            # this error the same as if the incoming value was a non-
            # matching ASCII value.
            #
            return get_currency(code=value.upper())
        except (CurrencyDoesNotExist, UnicodeDecodeError):
            return self._invalid_value(value, self.CODE_INVALID, exc_info=True)


class Locale(BaseFilter):
    """
    Ensures that incoming values are well-formed IETF language tags.

    The resulting value is a :py:class:`language_tags.Tag.Tag` object.
    """
    CODE_INVALID = 'not_ietf_language_tag'

    templates = {
        CODE_INVALID: 'This value is not a well-formed IETF language tag.',
    }

    def _apply(self, value):
        # Lazy-load dependencies to reduce memory usage when this
        # filter is not used in a project.
        from language_tags import tags
        from language_tags.Tag import Tag

        value = self._filter(value, Type(string_types + (Tag,)))

        if self._has_errors:
            return None

        if isinstance(value, Tag):
            return value

        tag = tags.tag(value)

        if not tag.valid:
            return self._invalid_value(
                value   = value,
                reason  = self.CODE_INVALID,

                context = {
                    'parse_errors': [
                        (error.code, error.message)
                            for error in tag.errors
                    ],
                },
            )

        return tag
