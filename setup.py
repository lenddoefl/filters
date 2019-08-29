from codecs import StreamReader, open
from os.path import dirname, join, realpath

from setuptools import setup

cwd = dirname(realpath(__file__))

##
# Load long description for PyPi.
with open(join(cwd, 'README.rst'), 'r', 'utf-8') as f: # type: StreamReader
    long_description = f.read()


tests_require = [
    'tox >= 3.7',
    'nose',
]


##
# Off we go!
# noinspection SpellCheckingInspection
setup(
    name        = 'phx-filters',
    description = 'Validation and data pipelines made easy!',
    url         = 'https://filters.readthedocs.io/',

    version = '2.0.0',

    packages = ['filters'],

    long_description = long_description,

    install_requires = [
        'phx-class-registry',
        'python-dateutil',
        'pytz',
        'regex >= 2018.8.17',
    ],

    extras_require = {
        # Extensions
        'django':['filters-django'],
        'iso': ['filters-iso'],

        # Utilities for Project Maintainers
        'docs-builder': ['sphinx', 'sphinx_rtd_theme'],
        'test-runner': tests_require,
    },

    test_suite    = 'test',
    test_loader   = 'nose.loader:TestLoader',
    tests_require = tests_require,

    license = 'MIT',

    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Text Processing :: Filters',
    ],

    keywords = 'data validation',

    author          = 'Phoenix Zerin',
    author_email    = 'phx@phx.ph',
)
