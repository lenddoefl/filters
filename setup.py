# coding=utf-8
# :bc: Not importing unicode_literals because in Python 2 distutils,
# some values are expected to be byte strings.
from __future__ import absolute_import, division, print_function

from codecs import StreamReader, open
from sys import version_info

from setuptools import setup


##
# Load long description for PyPi.
with open('README.rst', 'r', 'utf-8') as f: # type: StreamReader
    long_description = f.read()


##
# Certain dependencies are optional depending on Python version.
dependencies = [
    'iso3166',
    'language_tags',
    'py-moneyed',
    'python-dateutil',
    'pytz',
    'regex',
    'six',
    'typing',
]

if version_info[0] < 3:
    # noinspection SpellCheckingInspection
    dependencies.extend([
        'py2casefold',
    ])


##
# Off we go!
setup(
    name        = 'filters',
    description = 'Validation and data pipelines made easy!',
    url         = 'https://filters.readthedocs.io/',

    version = '1.1.6',

    packages = ['filters'],

    long_description = long_description,

    install_requires = dependencies,

    test_suite    = 'test',
    test_loader   = 'nose.loader:TestLoader',
    tests_require = [
        'nose',
    ],

    data_files = [
        ('', ['LICENSE']),
    ],

    license = 'MIT',

    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Text Processing :: Filters',
    ],

    keywords = 'data validation',

    author          = 'Phoenix Zerin',
    author_email    = 'phoenix.zerin@eflglobal.com',
)
