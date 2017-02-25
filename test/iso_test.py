# coding=utf-8
from __future__ import absolute_import, division, print_function, \
    unicode_literals

from iso3166 import Country, countries_by_alpha3
from language_tags import tags
from language_tags.Tag import Tag
from moneyed import Currency, get_currency
from six import text_type

import filters as f
from filters.test import BaseFilterTestCase


class CountryTestCase(BaseFilterTestCase):
    filter_type = f.Country

    def test_pass_none(self):
        """
        ``None`` always passes this filter.

        Use ``Required | Country`` if you want to reject ``None``.
        """
        self.assertFilterPasses(None)

    def test_pass_valid_alpha_3(self):
        """
        The incoming value is a valid ISO-3316-1 alpha-3 country code.
        """
        filtered = self._filter('FRA')

        self.assertFilterPasses(filtered, self.skip_value_check)

        country = filtered.cleaned_data
        self.assertIsInstance(country, Country)
        self.assertEqual(country.name, 'France')

    def test_pass_valid_alpha_2(self):
        """
        The incoming value is a valid ISO-3166-1 alpha-2 country code.
        """
        filtered = self._filter('IE')

        self.assertFilterPasses(filtered, self.skip_value_check)

        country = filtered.cleaned_data
        self.assertIsInstance(country, Country)
        self.assertEqual(country.name, 'Ireland')

    def test_pass_case_insensitive(self):
        """
        The incoming value is basically valid, but it has the wrong
        case.
        """
        filtered = self._filter('arg')

        self.assertFilterPasses(filtered, self.skip_value_check)

        country = filtered.cleaned_data
        self.assertIsInstance(country, Country)
        self.assertEqual(country.name, 'Argentina')

    def test_fail_invalid_code(self):
        """
        The incoming value is not a valid ISO-3316-1 country code.
        """
        # Surrender is not an option!
        self.assertFilterErrors('\u2690', [f.Country.CODE_INVALID])

    def test_fail_subdivision(self):
        """
        Subdivisions are not accepted, even though certain ones are
        technically part of ISO-3166-1.

        After all, the filter is named ``Country``, not ``ISO_3166_1``!
        """
        self.assertFilterErrors('IE-L', [f.Country.CODE_INVALID])

    def test_fail_wrong_type(self):
        """
        The incoming value is not a string.
        """
        self.assertFilterErrors(['CHN', 'JPN'], [f.Type.CODE_WRONG_TYPE])

    def test_pass_country_object(self):
        """
        The incoming value is already a :py:class:`Country` object.
        """
        self.assertFilterPasses(countries_by_alpha3.get('USA'))


class CurrencyTestCase(BaseFilterTestCase):
    filter_type = f.Currency

    def test_pass_none(self):
        """
        ``None`` always passes this filter.

        Use ``Required | Currency`` if you do want to reject ``None``.
        """
        self.assertFilterPasses(None)

    def test_pass_valid_code(self):
        """
        The incoming value is a valid ISO-4217 currency code.
        """
        filtered = self._filter('PEN')

        self.assertFilterPasses(filtered, self.skip_value_check)

        currency = filtered.cleaned_data
        self.assertIsInstance(currency, Currency)
        self.assertEqual(currency.name, 'Nuevo Sol')

    def test_pass_case_insensitive(self):
        """
        The incoming value is basically valid, but it has the wrong
        case.
        """
        filtered = self._filter('ars')

        self.assertFilterPasses(filtered, self.skip_value_check)

        currency = filtered.cleaned_data
        self.assertIsInstance(currency, Currency)
        self.assertEqual(currency.name, 'Argentine Peso')

    def test_fail_invalid_code(self):
        """
        The incoming value is not a valid ISO-4217 currency code.
        """
        # You can't use the currency symbol, silly!
        self.assertFilterErrors('\u00a3', [f.Currency.CODE_INVALID])

    def test_fail_wrong_type(self):
        """
        The incoming value is not a string.
        """
        self.assertFilterErrors(['USD', 'CNY'], [f.Type.CODE_WRONG_TYPE])

    def test_pass_currency_object(self):
        """
        The incoming value is already a :py:class:`moneyed.Currency`
        object.
        """
        self.assertFilterPasses(get_currency(code='USD'))


class LocaleTestCase(BaseFilterTestCase):
    """
    Note that unit tests will focus on the functionality of the Filter
    rather than the underlying library; the variety of formats and
    values that the Locale Filter accepts FAR exceeds the scope
    demonstrated in these tests.

    References:
      - http://r12a.github.io/apps/subtags/
      - https://pypi.python.org/pypi/language-tags
      - https://github.com/mattcg/language-tags
    """
    filter_type = f.Locale

    def test_pass_none(self):
        """
        ``None`` always passes this filter.

        Use `Required | Locale` if you want to reject `None`.
        """
        self.assertFilterPasses(None)

    def test_valid_locale(self):
        """
        Valid locale string is valid.
        """
        # There are a LOT of possible values that can go here.
        # http://r12a.github.io/apps/subtags/
        filtered = self._filter('en-cmn-Hant-HK')

        self.assertFilterPasses(filtered, self.skip_value_check)

        tag = filtered.cleaned_data

        self.assertIsInstance(tag, Tag)
        self.assertTrue(tag.valid)

        #
        # Language tags have LOTS of attributes.
        # We will check a few of them to make sure the Filter returned
        # the correct tag, but you should be aware that there is a
        # LOT of information available in the value returned by the
        # Locale Filter.
        #
        # For more information, check out the repo for the Javascript
        # version of the underlying `language_tags` library (the
        # Python version is a port with the same API... and no usage
        # documentation of its own).
        # https://github.com/mattcg/language-tags
        #
        self.assertEqual(text_type(tag), 'en-cmn-Hant-HK')
        self.assertEqual(text_type(tag.language), 'en')
        self.assertEqual(text_type(tag.region), 'HK')
        self.assertEqual(text_type(tag.script), 'Hant')

    def test_pass_case_insensitive(self):
        """
        The incoming value is basically valid, except it uses the wrong
        case.
        """
        filtered = self._filter('Az-ArAb-Ir')

        self.assertFilterPasses(filtered, self.skip_value_check)

        tag = filtered.cleaned_data

        self.assertIsInstance(tag, Tag)
        self.assertTrue(tag.valid)

        self.assertEqual(text_type(tag), 'az-Arab-IR')
        self.assertEqual(text_type(tag.language), 'az')
        self.assertEqual(text_type(tag.region), 'IR')
        self.assertEqual(text_type(tag.script), 'Arab')

    def test_fail_invalid_value(self):
        """
        The incoming value generates parsing errors.
        """
        # noinspection SpellCheckingInspection
        filtered = self._filter(
            'sl-Cyrl-YU-rozaj-solba-1994-b-1234-a-Foobar-x-b-1234-a-Foobar'
        )

        self.assertFilterErrors(filtered, [f.Locale.CODE_INVALID])

        # Parse errors included here for demonstration purposes.
        self.assertListEqual(
            filtered.filter_messages[''][0].context.get('parse_errors'),

            [
                # Sorry about the magic values.
                # These are defined in the Tag initializer, so they're
                # a bit tricky to get at without complicating the
                # test.
                # :py:meth:`Tag.__init__`
                (11, "The subtag 'YU' is deprecated."),
                (8, "Duplicate variant subtag 'solba' found."),
                (8, "Duplicate variant subtag '1994' found."),
            ],
        )

    def test_fail_wrong_type(self):
        """
        The incoming value is not a string.
        """
        self.assertFilterErrors(['en', 'US'], [f.Type.CODE_WRONG_TYPE])

    def test_pass_tag_object(self):
        """
        The incoming value is already a Tag object.
        """
        self.assertFilterPasses(tags.tag('en-cmn-Hant-HK'))
