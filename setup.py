# coding=utf-8
from __future__ import absolute_import, division, print_function, \
    unicode_literals

from codecs import StreamReader, open
from setuptools import setup


with open('README.rst', 'r', 'utf-8') as f: # type: StreamReader
    long_description = f.read()

# noinspection SpellCheckingInspection
setup(
    name        = 'filters',
    description = 'Validation and data pipelines made easy!',
    url         = 'https://github.com/eflglobal/filters/',

    # Don't forget to update version number in `filters/__init__.py`!
    version = '1.0.2',

    packages = ['filters'],

    long_description = long_description,

    install_requires = [
        'py2casefold ; python_version < "3"',
        'python-dateutil',
        'pytz',
        'regex',
        'six',
        'typing ; python_version < "3.5"',
    ],

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
