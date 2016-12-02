# coding=utf-8
from __future__ import absolute_import, division, print_function, \
    unicode_literals

from setuptools import setup

# noinspection SpellCheckingInspection
setup(
    name        = 'Filters',
    description = 'Data pipelines made easy!',
    url         = 'https://github.com/eflglobal/filters/',
    version     = '1.0.0',
    packages    = ['filters'],

    install_requires = [
        'py2casefold ; python_version < "3"',
        'python-dateutil',
        'pytz',
        'regex',
        'six',
        'typing ; python_version < "3.5"',
    ],

    data_files = [
        ('', ['LICENSE']),
    ],

    licence = 'MIT',

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
