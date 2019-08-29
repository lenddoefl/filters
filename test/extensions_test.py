from os.path import dirname
from unittest import TestCase

from pkg_resources import working_set

from filters.extensions import FilterExtensionRegistry
from filters.macros import FilterMacroType
from test import TestFilterAlpha, TestFilterBravo


def setUpModule():
    #
    # Install a fake distribution that we can use to inject entry
    # points at runtime.
    #
    # The side effects from this are pretty severe, but they (very
    # probably) only impact this test, and they are undone as soon as
    # the process terminates.
    #
    working_set.add_entry(dirname(__file__))


class FilterExtensionRegistryTestCase(TestCase):
    def test_happy_path(self):
        """
        Loading filters automatically via entry points.

        References:
          - /test/_support/filter_extension.egg-info/entry_points.txt
          - :py:func:`setUpModule`
        """
        # For this test, we will use a different entry point key, to
        # minimize the potential for side effects.
        registry = FilterExtensionRegistry('filters.extensions_test')

        # Note that the filters are registered using the entry point
        # names, which conventionally matches the class name (but it
        # doesn't strictly have to).
        alpha = registry.Alfred
        self.assertIs(alpha, TestFilterAlpha)

        # You can also instantiate filters using parameters.
        bravo = registry.Bruce(name='Batman')
        self.assertIsInstance(bravo, TestFilterBravo)
        self.assertEqual(bravo.name, 'Batman')

        # I couldn't find any Batman characters whose name begins with
        # C... and "Commissioner Gordon" doesn't count!
        charlie = registry.Catwoman
        # Note that :py:data:`test.TestFilterCharlie` is a filter
        # macro.
        self.assertTrue(issubclass(charlie, FilterMacroType))

        # Check that the correct number of extension filters were
        # registered.
        self.assertEqual(len(registry), 3)
