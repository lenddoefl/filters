from collections import OrderedDict, namedtuple

import filters as f
from filters.test import BaseFilterTestCase


class FilterChainTestCase(BaseFilterTestCase):
    def test_implicit_chain(self):
        """
        Chaining two filters together creates a FilterChain.
        """
        self.filter_type = lambda: f.Int | f.Max(3)

        self.assertFilterPasses('1', 1)
        self.assertFilterErrors('4', [f.Max.CODE_TOO_BIG])

    def test_implicit_chain_null(self):
        """
        Chaining a filter with ``None`` also yields a FilterChain, but
        unsurprisingly, the chain only contains the one filter.
        """
        filter_chain = f.Int() | None
        self.assertIsInstance(filter_chain, f.FilterChain)

        with self.assertRaises(f.FilterError):
            filter_chain.apply('not an int')

    # noinspection SpellCheckingInspection
    def test_chainception(self):
        """
        You can also chain FilterChains together.
        """
        fc1 = f.NotEmpty | f.Choice(choices=('Lucky', 'Dusty', 'Ned'))
        fc2 = f.NotEmpty | f.MinLength(4)

        self.filter_type = lambda: fc1 | fc2

        self.assertFilterPasses('Lucky')
        self.assertFilterErrors('El Guapo', [f.Choice.CODE_INVALID])
        self.assertFilterErrors('Ned', [f.MinLength.CODE_TOO_SHORT])

    def test_stop_after_invalid_value(self):
        """
        A FilterChain stops processing the incoming value after any
        filter fails.
        """
        # This FilterChain will pretty much reject anything that you
        # throw at it.
        self.filter_type = \
            lambda: f.MaxLength(3) | f.MinLength(8) | f.Required

        # Note that the value 'foobar' fails both the MaxLength and the
        # MinLength filters, but the FilterChain stops processing
        # after MaxLength fails.
        self.assertFilterErrors('foobar', [f.MaxLength.CODE_TOO_LONG])


class FilterRepeaterTestCase(BaseFilterTestCase):
    def test_pass_none(self):
        """
        For consistency with all the other Filter classes, `None` is
        considered a valid value to pass to a FilterRepeater, even
        though it is not iterable.
        """
        self.filter_type = lambda: f.FilterRepeater(f.Int)

        self.assertFilterPasses(None)

    def test_pass_iterable(self):
        """
        A FilterRepeater is applied to a list of valid values.
        """
        self.filter_type = lambda: f.FilterRepeater(f.NotEmpty | f.Int)

        self.assertFilterPasses(
            ['1', 2, 0, None, '-12'],
            [1, 2, 0, None, -12],
        )

    def test_fail_iterable(self):
        """
        A FilterRepeater is applied to a list that contains invalid
        values.
        """
        self.filter_type = lambda: f.FilterRepeater(f.NotEmpty | f.Int)

        self.assertFilterErrors(
            # First element is valid (control group).
            # The rest fail miserably.
            [4, 'NaN', 3.14, 'FOO', ''],

            {
                '1': [f.Decimal.CODE_NON_FINITE],
                '2': [f.Int.CODE_DECIMAL],
                '3': [f.Decimal.CODE_INVALID],
                '4': [f.NotEmpty.CODE_EMPTY],
            },

            expected_value=[4, None, None, None, None],
        )

    def test_pass_mapping(self):
        """
        A FilterRepeater is applied to a dict of valid values.
        """
        self.filter_type = lambda: f.FilterRepeater(f.NotEmpty | f.Int)

        self.assertFilterPasses(
            {
                'foo':      '1',
                'bar':      2,
                'baz':      None,
                'luhrmann': '-12',
            },

            # The FilterRepeater applies the filter chain to the dict's
            # values.  Note that it completely ignores the keys.
            {
                'foo':      1,
                'bar':      2,
                'baz':      None,
                'luhrmann': -12,
            },
        )

    def test_fail_mapping(self):
        """
        A FilterRepeater is applied to a dict that contains invalid
        values.
        """
        self.filter_type = lambda: f.FilterRepeater(f.NotEmpty | f.Int)

        self.assertFilterErrors(
            {
                # First element is valid (control group).
                # The rest fail miserably.
                'foo':      4,
                'bar':      'NaN',
                'baz':      3.14,
                'luhrmann': 'FOO',
            },

            {
                'bar':      [f.Decimal.CODE_NON_FINITE],
                'baz':      [f.Int.CODE_DECIMAL],
                'luhrmann': [f.Decimal.CODE_INVALID],
            },

            # Just as with collections, the invalid values in the
            # filtered value are replaced with `None`.
            expected_value={
                'foo':      4,
                'bar':      None,
                'baz':      None,
                'luhrmann': None,
            },
        )

    def test_restrict_keys(self):
        """
        A FilterRepeated is configured to restrict allowed keys in a
        mapping.
        """
        self.filter_type = lambda: f.FilterRepeater(
            filter_chain=f.Int,
            restrict_keys={'ducks', 'sea otters'},
        )

        # As long as you stick to the expected keys, everything's
        # hunky-dory.
        self.assertFilterPasses(
            {'ducks': '3', 'sea otters': '4'},
            {'ducks': 3, 'sea otters': 4},
        )

        # However, should you deviate from the marked path, we cannot
        # be held responsible for the consequences.
        self.assertFilterErrors(
            # Charlie shot first!
            {'ducks': '3', 'hawks': '4'},

            {
                'hawks': [f.FilterRepeater.CODE_EXTRA_KEY],
            },

            # Invalid keys are not included in the filtered value.
            # This is very similar to how FilterMapper works.
            expected_value={
                'ducks': 3,
            }
        )

    def test_restrict_indexes(self):
        """
        A FilterRepeater CAN be configured to restrict keys for
        incoming Iterables, although it is probably the wrong tool
        for the job (MaxLength is probably a better fit).
        """
        #
        # Note that if `restrict_keys` contains non-integers and/or
        # starts with a value other than 0, the FilterRepeater will
        # reject EVERY Iterable it comes across!
        #
        # Really, you should just stick a MaxLength(2) in front of the
        # FilterRepeater and call it a day.  It's less likely to
        # introduce a logic bug and way easier for other devs to
        # interpret.
        #
        # noinspection PyTypeChecker
        self.filter_type = lambda: f.FilterRepeater(
            filter_chain=f.Int,
            restrict_keys={0, 1, 3, 4},
        )

        self.assertFilterPasses(['4', '3'], [4, 3])

        self.assertFilterErrors(
            ['50', '40', '30', '20', '10'],

            {
                # Index 2 was unexpected (the Filter is configured
                # only to allow indexes 0, 1, 3 and 4).
                '2': [f.FilterRepeater.CODE_EXTRA_KEY],
            },

            # To make things even more confusing, the invalid "keys"
            # (indexes) ARE included in the filtered value.  This is
            # because, unlike in mappings, it is not possible to
            # identify "missing" indexes.
            expected_value=[50, 40, None, 20, 10]
        )

        # The moral of the story is, don't use `restrict_keys` when
        # configuring a FilterRepeater that will operate on
        # collections.

    def test_fail_non_iterable_value(self):
        """
        A FilterRepeater will reject any non-iterable value it comes
        across (except for `None`).
        """
        self.filter_type = lambda: f.FilterRepeater(f.Int)

        self.assertFilterErrors(42, [f.Type.CODE_WRONG_TYPE])

    def test_repeater_chained_with_repeater(self):
        """
        Chaining two FilterRepeaters together has basically the same
        effect as combining their Filters, except for one very
        important difference:  The two sets of Filters are applied
        in sequence.

        That is, the second set of Filters only get applied if ALL
        of the Filters in the first set pass!

        Generally, combining two FilterRepeaters into a single instance
        is much easier to read/maintain than chaining them, but
        should you ever come across a situation where you need to
        apply two FilterRepeaters in sequence, you can do so.
        """
        self.filter_type = \
            lambda: f.FilterRepeater(f.NotEmpty) | f.FilterRepeater(
                f.Int)

        # The values in this list pass through both FilterRepeaters
        # successfully.
        self.assertFilterPasses(
            ['1', 2, 0, None, '-12'],
            [1, 2, 0, None, -12],
        )

        # The values in this list fail one or more Filters in each
        # FilterRepeater.
        self.assertFilterErrors(
            ['', 'NaN', 0, None, 'FOO'],

            {
                # Fails the NotEmpty filter in the first FilterRepeater.
                '0': [f.NotEmpty.CODE_EMPTY],

                # IMPORTANT:  Because the first FilterRepeater had one
                # or more errors, the outer FilterChain stopped.
                # # Fails the Int filter in the second FilterRepeater.
                # '1': [f.Decimal.CODE_NON_FINITE],
                # '4': [f.Int.CODE_INVALID],
            },

            # The result is the same as if we only ran the value
            # through the first FilterRepeater.
            expected_value=[
                None, 'NaN', 0, None, 'FOO'
            ]
        )

        # The values in this list pass the first FilterRepeater but
        # fail the second one.
        self.assertFilterErrors(
            ['1', 'NaN', 0, None, 'FOO'],

            {
                '1': [f.Decimal.CODE_NON_FINITE],
                '4': [f.Decimal.CODE_INVALID],
            },

            expected_value=[1, None, 0, None, None],
        )

    def test_repeater_chained_with_filter(self):
        """
        Chaining a Filter with a FilterRepeater causes the chained
        Filter to operate on the entire collection.
        """
        # This chain will apply NotEmpty to every item in the
        # collection, and then apply MaxLength to the collection as a
        # whole.
        self.filter_type = \
            lambda: f.FilterRepeater(f.NotEmpty) | f.MaxLength(2)

        # The collection has a length of 2, so it passes the MaxLength
        # filter.
        self.assertFilterPasses(['foo', 'bar'])

        # The collection has a length of 3, so it fails the MaxLength
        # filter.
        self.assertFilterErrors(
            ['a', 'b', 'c'],
            [f.MaxLength.CODE_TOO_LONG],
        )

    # noinspection SpellCheckingInspection
    def test_repeaterception(self):
        """
        FilterRepeaters can contain other FilterRepeaters.
        """
        self.filter_type = lambda: (
            # Apply the following filters to each item in the incoming
            # value:
            f.FilterRepeater(

                # 1. It must be a list.
                f.Type(list)

                # 2. Apply the Int filter to each of its items.
                | f.FilterRepeater(f.Int)

                # 3. It must have a length <= 3.
                | f.MaxLength(3)
            )
        )

        self.assertFilterPasses(
            #
            # Note that the INCOMING VALUE ITSELF does not have to be a
            # list, nor does it have to have a max length <= 3.
            #
            # These Filters are applied to the items INSIDE THE
            # INCOMING VALUE (because of the outer FilterRepeater).
            #
            {
                'foo':      ['1', '2', '3'],
                'bar':      [-20, 20],
                'baz':      ['486'],
                'luhrmann': [None, None, None],
            },

            {
                'foo':      [1, 2, 3],
                'bar':      [-20, 20],
                'baz':      [486],
                'luhrmann': [None, None, None],
            },
        )

        # The 1st item in this value is not a list, so it fails.
        self.assertFilterErrors(
            [
                [42],
                {'arch': 486},
            ],

            {
                '1': [f.Type.CODE_WRONG_TYPE],
            },

            expected_value=[[42], None],
        )

        # The 1st item in this value contains invalid ints.
        self.assertFilterErrors(
            [
                [42],
                ['NaN', 3.14, 'FOO'],
            ],

            {
                #
                # The error keys are the dotted paths to the invalid
                # values (in this case, they are numeric because we
                # are working with lists).
                #
                # This way, we don't have to deal with nested dicts
                # when processing error codes.
                #
                '1.0': [f.Decimal.CODE_NON_FINITE],
                '1.1': [f.Int.CODE_DECIMAL],
                '1.2': [f.Decimal.CODE_INVALID],
            },

            expected_value=[[42], [None, None, None]],
        )

        # The 1st item in this value is too long.
        self.assertFilterErrors(
            [
                [42],
                [1, 2, 3, 4]
            ],

            {
                '1': [f.MaxLength.CODE_TOO_LONG],
            },

            expected_value=[[42], None]
        )


class FilterMapperTestCase(BaseFilterTestCase):
    def test_pass_none(self):
        """
        For consistency with all the other Filter classes, `None` is
        considered a valid value to pass to a FilterMapper, even
        though it is not iterable.
        """
        self.filter_type = lambda: f.FilterMapper({'id': f.Int})

        self.assertFilterPasses(None)

    def test_pass_mapping(self):
        """
        A FilterRepeater is applied to a dict containing valid values.
        """
        self.filter_type = lambda: f.FilterMapper({
            'id':      f.Required | f.Int | f.Min(1),
            'subject': f.NotEmpty | f.MaxLength(16),
        })

        filter_ = self._filter({
            'id':      '42',
            'subject': 'Hello, world!',
        })

        self.assertFilterPasses(
            filter_,

            {
                'id':      42,
                'subject': 'Hello, world!',
            },
        )

        # The result is a dict, to match the type of the filter map.
        self.assertIs(type(filter_.cleaned_data), dict)

    def test_pass_ordered_mapping(self):
        """
        Configuring the FilterRepeater to return an OrderedDict.
        """
        # Note that we pass an OrderedDict to the filter initializer.
        self.filter_type = lambda: f.FilterMapper(OrderedDict((
            ('subject', f.NotEmpty | f.MaxLength(16)),
            ('id', f.Required | f.Int | f.Min(1)),
        )))

        filter_ = self._filter({
            'id':      '42',
            'subject': 'Hello, world!',
        })

        self.assertFilterPasses(
            filter_,

            OrderedDict((
                ('subject', 'Hello, world!'),
                ('id', 42),
            )),
        )

        # The result is an OrderedDict, to match the type of the filter
        # map.
        self.assertIs(type(filter_.cleaned_data), OrderedDict)

    def test_fail_mapping(self):
        """
        A FilterRepeater is applied to a dict containing invalid
        values.
        """
        self.filter_type = lambda: f.FilterMapper({
            'id':      f.Required | f.Int | f.Min(1),
            'subject': f.NotEmpty | f.MaxLength(16),
        })

        self.assertFilterErrors(
            {
                'id':      None,
                'subject': 'Antidisestablishmentarianism',
            },

            {
                'id':      [f.Required.CODE_EMPTY],
                'subject': [f.MaxLength.CODE_TOO_LONG],
            },

            expected_value={
                'id':      None,
                'subject': None,
            }
        )

    def test_extra_keys_allowed(self):
        """
        By default, FilterMappers passthru extra keys.
        """
        self.filter_type = lambda: f.FilterMapper({
            'id':      f.Required | f.Int | f.Min(1),
            'subject': f.NotEmpty | f.MaxLength(16),
        })

        self.assertFilterPasses(
            {
                'id':      '42',
                'subject': 'Hello, world!',
                'extra':   'ignored',
            },

            {
                'id':      42,
                'subject': 'Hello, world!',
                'extra':   'ignored',
            }
        )

    def test_extra_keys_ordered(self):
        """
        When the filter map is an OrderedDict, extra keys are
        alphabetized.
        """
        # Note that we pass an OrderedDict to the filter initializer.
        self.filter_type = lambda: f.FilterMapper(OrderedDict((
            ('subject', f.NotEmpty | f.MaxLength(16)),
            ('id', f.Required | f.Int | f.Min(1)),
        )))

        filter_ = self._filter({
            'id':      '42',
            'subject': 'Hello, world!',
            'cat':     'felix',
            'bird':    'phoenix',
            'fox':     'fennecs',
        })

        self.assertFilterPasses(
            filter_,

            OrderedDict((
                # The filtered keys are always listed first.
                ('subject', 'Hello, world!'),
                ('id', 42),

                    # Extra keys are listed afterward, in alphabetical
                    # order.
                ('bird', 'phoenix'),
                ('cat', 'felix'),
                ('fox', 'fennecs'),
            )),
        )

    def test_extra_keys_disallowed(self):
        """
        FilterMappers can be configured to treat any extra key as an
        invalid value.
        """
        self.filter_type = lambda: f.FilterMapper(
            {
                'id':      f.Required | f.Int | f.Min(1),
                'subject': f.NotEmpty | f.MaxLength(16),
            },

            # Treat all extra keys as invalid values.s
            allow_extra_keys=False,
        )

        self.assertFilterErrors(
            {
                'id':      '42',
                'subject': 'Hello, world!',
                'extra':   'ignored',
            },

            {
                'extra': [f.FilterMapper.CODE_EXTRA_KEY],
            },

            # The valid fields were still included in the return value,
            # but the invalid field was removed.
            expected_value={
                'id':      42,
                'subject': 'Hello, world!',
            }
        )

    def test_extra_keys_specified(self):
        """
        FilterMappers can be configured only to allow certain extra
        keys.
        """
        self.filter_type = lambda: f.FilterMapper(
            {
                'id':      f.Required | f.Int | f.Min(1),
                'subject': f.NotEmpty | f.MaxLength(16),
            },

            allow_extra_keys={'message', 'extra'},
        )

        # As long as the extra keys are in the FilterMapper's
        # ``allow_extra_keys`` setting, everything is fine.
        self.assertFilterPasses(
            {
                'id':      '42',
                'subject': 'Hello, world!',
                'extra':   'ignored',
            },

            {
                'id':      42,
                'subject': 'Hello, world!',
                'extra':   'ignored',
            },
        )

        # But, add a key that isn't in ``allow_extra_keys``, and you've
        # got a problem.
        self.assertFilterErrors(
            {
                'id':         '42',
                'subject':    'Hello, world!',
                'attachment': {
                    'type': 'image/jpeg',
                    'data': '...',
                },
            },

            {
                'attachment': [f.FilterMapper.CODE_EXTRA_KEY],
            },

            expected_value={
                'id':      42,
                'subject': 'Hello, world!',
            }
        )

    def test_missing_keys_allowed(self):
        """
        By default, FilterMappers treat missing keys as `None`.
        """
        self.filter_type = lambda: f.FilterMapper({
            'id':      f.Required | f.Int | f.Min(1),
            'subject': f.NotEmpty | f.MaxLength(16),
        })

        # 'subject' allows null values, so no errors are generated.
        self.assertFilterPasses(
            {
                'id': '42',
            },

            {
                'id':      42,
                'subject': None,
            },
        )

        # However, 'id' has Required in its FilterChain, so a missing
        # 'id' is still an error.
        self.assertFilterErrors(
            {
                'subject': 'Hello, world!',
            },

            {
                'id': [f.Required.CODE_EMPTY],
            },

            expected_value={
                'id':      None,
                'subject': 'Hello, world!',
            },
        )

    def test_missing_keys_disallowed(self):
        """
        FilterMappers can be configured to treat missing keys as
        invalid values.
        """
        self.filter_type = lambda: f.FilterMapper(
            {
                'id':      f.Required | f.Int | f.Min(1),
                'subject': f.NotEmpty | f.MaxLength(16),
            },

            # Treat missing keys as invalid values.
            allow_missing_keys=False,
        )

        self.assertFilterErrors(
            {},

            {
                'id':      [f.FilterMapper.CODE_MISSING_KEY],
                'subject': [f.FilterMapper.CODE_MISSING_KEY],
            },

            expected_value={
                'id':      None,
                'subject': None,
            },
        )

    def test_missing_keys_specified(self):
        """
        FilterMappers can be configured to allow some missing keys but
        not others.
        """
        self.filter_type = lambda: f.FilterMapper(
            {
                'id':      f.Required | f.Int | f.Min(1),
                'subject': f.NotEmpty | f.MaxLength(16),
            },

            allow_missing_keys={'subject'},
        )

        # The FilterMapper is configured to treat missing 'subject' as
        # if it were set to `None`.
        self.assertFilterPasses(
            {
                'id': '42'
            },

            {
                'id':      42,
                'subject': None,
            },
        )

        # However, 'id' is still required.
        self.assertFilterErrors(
            {
                'subject': 'Hello, world!',
            },

            {
                'id': [f.FilterMapper.CODE_MISSING_KEY],
            },

            expected_value={
                'id':      None,
                'subject': 'Hello, world!',
            }
        )

    def test_passthru_key(self):
        """
        If you want to make a key required but do not want to run any
        Filters on it, set its FilterChain to `None`.
        """
        self.filter_type = lambda: f.FilterMapper(
            {
                'id':      f.Required | f.Int | f.Min(1),
                'subject': None,
            },

            # If you configure a FilterMapper with passthru keys(s),
            # you generally also want to disallow missing keys.
            allow_missing_keys=False,
        )

        self.assertFilterPasses(
            {
                'id':      '42',
                'subject': 'Hello, world!',
            },

            {
                'id':      42,
                'subject': 'Hello, world!',
            },
        )

        self.assertFilterPasses(
            {
                'id':      '42',
                'subject': None,
            },

            {
                'id':      42,
                'subject': None,
            },
        )

        self.assertFilterErrors(
            {
                'id': '42',
            },

            {
                'subject': [f.FilterMapper.CODE_MISSING_KEY],
            },

            expected_value={
                'id':      42,
                'subject': None,
            },
        )

    def test_fail_non_mapping(self):
        """The incoming value is not a mapping."""
        self.filter_type = lambda: f.FilterMapper({
            'id':      f.Required | f.Int | f.Min(1),
            'subject': f.NotEmpty | f.MaxLength(16),
        })

        self.assertFilterErrors(
            # Nope; it's gotta be an explicit mapping.
            (('id', '42'), ('subject', 'Hello, world!')),
            [f.Type.CODE_WRONG_TYPE],
        )

    def test_mapper_chained_with_mapper(self):
        """
        Chaining two FilterMappers together has basically the same
        effect as combining their Filters.

        Generally, combining two FilterMappers into a single instance
        is much easier to read/maintain than chaining them, but in
        a few cases it may be unavoidable (for example, if you need
        each FilterMapper to handle extra and/or missing keys
        differently).
        """
        fm1 = f.FilterMapper(
            {
                'id': f.Int | f.Min(1),
            },

            allow_missing_keys=True,
            allow_extra_keys=True,
        )

        fm2 = f.FilterMapper(
            {
                'id':      f.Required | f.Max(256),
                'subject': f.NotEmpty | f.MaxLength(16),
            },

            allow_missing_keys=False,
            allow_extra_keys=False,
        )

        self.filter_type = lambda: fm1 | fm2

        self.assertFilterPasses(
            {
                'id':      '42',
                'subject': 'Hello, world!',
            },

            {
                'id':      42,
                'subject': 'Hello, world!',
            },
        )

        self.assertFilterErrors(
            {},

            {
                # ``fm1`` allows missing keys, so it sets 'id' to
                # ``None``.
                # However, ``fm2`` does not allow ``None`` for 'id'
                # (because of the ``Required`` filter).
                'id':      [f.Required.CODE_EMPTY],

                # `fm1` does not care about `subject`, but `fm2`
                # expects it to be there.
                'subject': [f.FilterMapper.CODE_MISSING_KEY],
            },

            expected_value={
                'id':      None,
                'subject': None,
            },
        )

    def test_filter_mapper_chained_with_filter(self):
        """
        Chaining a Filter with a FilterMapper causes the chained Filter
        to operate on the entire mapping.
        """
        fm = f.FilterMapper({
            'id':      f.Required | f.Int | f.Min(1),
            'subject': f.NotEmpty | f.MaxLength(16),
        })

        self.filter_type = lambda: fm | f.MaxLength(3)

        self.assertFilterPasses(
            {
                'id':      '42',
                'subject': 'Hello, world!',
                'extra':   'ignored',
            },

            {
                'id':      42,
                'subject': 'Hello, world!',
                'extra':   'ignored',
            },
        )

        self.assertFilterErrors(
            {
                'id':         '42',
                'subject':    'Hello, world!',
                'extra':      'ignored',
                'attachment': None,
            },

            # The incoming value has 4 items, which fails the MaxLength
            # filter.
            [f.MaxLength.CODE_TOO_LONG],
        )

    # noinspection SpellCheckingInspection
    def test_mapperception(self):
        """
        Want to filter dicts that contain other dicts?
        We need to go deeper.
        """
        self.filter_type = lambda: f.FilterMapper(
            {
                'id':         f.Required | f.Int | f.Min(1),
                'subject':    f.NotEmpty | f.MaxLength(16),
                'attachment': f.FilterMapper(
                    {
                        'type':
                                f.Required
                                | f.Choice(
                                    choices={'image/jpeg', 'image/png'}),

                        'data': f.Required | f.Base64Decode,
                    },

                    allow_extra_keys=False,
                    allow_missing_keys=False,
                )
            },

            allow_extra_keys=False,
            allow_missing_keys=False,
        )

        # Valid mapping is valid.
        self.assertFilterPasses(
            {
                'id':         '42',
                'subject':    'Hello, world!',

                'attachment': {
                    'type': 'image/jpeg',

                    'data':
                            b'R0lGODlhDwAPAKECAAAAzMzM/////wAAACwAAAAAD'
                            b'wAPAAACIISPeQHsrZ5ModrLlN48CXF8m2iQ3YmmKq'
                            b'VlRtW4MLwWACH+EVRIRSBDQUtFIElTIEEgTElFOw==',
                },
            },

            {
                'id':         42,
                'subject':    'Hello, world!',

                'attachment': {
                    'type': 'image/jpeg',

                    'data':
                            b'GIF89a\x0f\x00\x0f\x00\xa1\x02\x00\x00\x00'
                            b'\xcc\xcc\xcc\xff\xff\xff\xff\x00\x00\x00,\x00'
                            b'\x00\x00\x00\x0f\x00\x0f\x00\x00\x02 \x84\x8f'
                            b'y\x01\xec\xad\x9eL\xa1\xda\xcb\x94\xde<\tq|'
                            b'\x9bh\x90\xdd\x89\xa6*\xa5eF\xd5\xb80\xbc\x16'
                            b'\x00!\xfe\x11THE CAKE IS A LIE;'
                },
            },
        )

        # Invalid mapping... not so much.
        self.assertFilterErrors(
            {
                'id':         'NaN',

                'attachment': {
                    'type': 'foo',
                    'data': False,
                },
            },

            {
                # The error keys are the dotted paths to the invalid
                # values.
                # This way, we don't have to deal with nested dicts
                # when processing error codes.
                'id':              [f.Decimal.CODE_NON_FINITE],
                'subject':         [f.FilterMapper.CODE_MISSING_KEY],
                'attachment.type': [f.Choice.CODE_INVALID],
                'attachment.data': [f.Type.CODE_WRONG_TYPE],
            },

            # The resulting value has the expected structure, but it's
            # a ghost town.
            expected_value={
                'id':         None,
                'subject':    None,

                'attachment': {
                    'type': None,
                    'data': None,
                },
            },
        )


Color = namedtuple('Color', ('r', 'g', 'b'))


class NamedTupleTestCase(BaseFilterTestCase):
    @staticmethod
    def filter_type():
        return f.NamedTuple(Color)

    def test_success_none(self):
        """
        ``None`` always passes this filter.

        Chain with :py:class:`f.Required` if you want to disallow null
        values.
        """
        self.assertFilterPasses(None)

    def test_success_namedtuple_correct_type(self):
        """
        Incoming value is already a namedtuple of the expected type.
        """
        self.assertFilterPasses(Color(64, 128, 192))

    def test_success_namedtuple_different_type(self):
        """
        Incoming value is a namedtuple instance, but of a different
        type.

        Since namedtuples are still tuples, this has the same result as
        for any other incoming iterable.
        """
        # Just to be tricky, we'll make it look very close to the
        # expected type.
        AltColor = namedtuple('AltColor', Color._fields)

        self.assertFilterPasses(
            AltColor(64, 128, 192),
            Color(64, 128, 192),
        )

    def test_success_iterable(self):
        """
        Incoming value is an iterable with correct values.
        """
        value = [64, 128, 192]
        self.assertFilterPasses(value, Color(*value))

    def test_success_iterable_compat(self):
        """
        Incoming value is an iterable, formatted for compatibility with
        Python < 3.6.
        """
        value = [('b', 192), ('g', 128), ('r', 64)]
        self.assertFilterPasses(value, Color(*value))

    def test_success_mapping(self):
        """
        Incoming value is a mapping with correct keys.
        """
        value = {'r': 64, 'g': 128, 'b': 192}
        self.assertFilterPasses(value, Color(**value))

    def test_fail_incompatible_type(self):
        """
        Incoming value has a type that we cannot work with.
        """
        self.assertFilterErrors(42, [f.Type.CODE_WRONG_TYPE])

    def test_fail_iterable_too_short(self):
        """
        Incoming value is an iterable that is missing one or more
        values.
        """
        self.assertFilterErrors((64, 128,), [f.MinLength.CODE_TOO_SHORT])

    def test_fail_iterable_too_long(self):
        """
        Incoming value is an iterable that has too many values.
        """
        self.assertFilterErrors(
            (64, 128, 192, 0.5),
            [f.MaxLength.CODE_TOO_LONG],
        )

    def test_fail_mapping_missing_keys(self):
        """
        Incoming value is a mapping that is missing one or more keys.
        """
        self.assertFilterErrors(
            {},

            {
                'r': [f.FilterMapper.CODE_MISSING_KEY],
                'g': [f.FilterMapper.CODE_MISSING_KEY],
                'b': [f.FilterMapper.CODE_MISSING_KEY],
            },
        )

    def test_fail_mapping_extra_keys(self):
        """
        Incoming value is a mapping that has extra keys that we don't
        know what to do with.
        """
        self.assertFilterErrors(
            {
                'r': 64,
                'g': 128,
                'b': 192,
                'a': 0.5,
            },

            {
                'a': [f.FilterMapper.CODE_EXTRA_KEY],
            },
        )

    def test_success_filter_map(self):
        """
        Applying a :py:class:`f.FilterMap` to the values in a namedtuple
        after converting (success case).
        """
        self.filter_type = lambda: f.NamedTuple(Color, {
            # For whatever reason, we decide not to filter ``r``.
            'g': f.Required | f.Int | f.Min(0) | f.Max(255),
            'b': f.Required | f.Int | f.Min(0) | f.Max(255),
        })

        self.assertFilterPasses(
            ('64.0', '128', 192.0),
            Color('64.0', 128, 192),
        )

    def test_fail_filter_map(self):
        """
        Applying a :py:class:`f.FilterMap` to the values in a namedtuple
        after converting (failure case).
        """
        self.filter_type = lambda: f.NamedTuple(Color, {
            # For whatever reason, we decide not to filter ``r``.
            'g': f.Required | f.Int | f.Min(0) | f.Max(255),
            'b': f.Required | f.Int | f.Min(0) | f.Max(255),
        })

        self.assertFilterErrors(
            ['NaN', None, (42,)],

            {
                'g': [f.Required.CODE_EMPTY],
                'b': [f.Decimal.CODE_INVALID],
            },
        )


class FilterSwitchTestCase(BaseFilterTestCase):
    filter_type = f.FilterSwitch

    def test_pass_none(self):
        """
        ``None`` always passes this filter.

        Use ``f.Required | f.FilterSwitch`` to reject null values.
        """
        self.assertFilterPasses(
            self._filter(
                None,

                getter=lambda value: value['anything'],
                cases={},
            ),
        )

    def test_pass_match_case(self):
        """
        The incoming value matches one of the switch cases.
        """
        self.assertFilterPasses(
            self._filter(
                {'name': 'positive', 'value': 42},

                getter=lambda value: value['name'],
                cases={
                    'positive': f.FilterMapper({'value': f.Int | f.Min(0)}),
                },
            ),
        )

    def test_fail_match_case(self):
        """
        The incoming value matches one of the switch cases, but it is
        not valid, according to the corresponding filter.
        """
        self.assertFilterErrors(
            self._filter(
                {'name': 'positive', 'value': -1},

                getter=lambda value: value['name'],
                cases={
                    'positive': f.FilterMapper({'value': f.Int | f.Min(0)}),
                },
            ),
            {'value': [f.Min.CODE_TOO_SMALL]},

            # The result is the exact same as if the value were passed
            # directly to the corresponding filter.
            expected_value={'name': 'positive', 'value': None},
        )

    def test_pass_default(self):
        """
        The incoming value does not match any of the switch cases, but
        we defined a default filter.
        """
        self.assertFilterPasses(
            self._filter(
                {'name': 'negative', 'value': -42},

                getter=lambda value: value['name'],
                cases={
                    'positive': f.FilterMapper({'value': f.Int | f.Min(0)}),
                },
                default=f.FilterMapper({'value': f.Int | f.Max(0)}),
            ),
        )

    def test_fail_no_default(self):
        """
        The incoming value does not match any of the switch cases, and
        we did not define a default filter.
        """
        self.assertFilterErrors(
            self._filter(
                {'name': 'negative', 'value': -42},

                getter=lambda value: value['name'],
                cases={
                    'positive': f.FilterMapper({'value': f.Int | f.Min(0)}),
                },
            ),

            [f.Choice.CODE_INVALID],
        )
