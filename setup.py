###
 # Copyright (c) 2014 Bert JW Regeer;
 #
 # Permission to use, copy, modify, and distribute this software for any
 # purpose with or without fee is hereby granted, provided that the above
 # copyright notice and this permission notice appear in all copies.
 #
 # THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 # WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 # MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 # ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 # WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 # ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 # OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
###

import os
import sys

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
try:
    with open(os.path.join(here, 'README.txt')) as f:
        README = f.read()
    with open(os.path.join(here, 'CHANGES.txt')) as f:
        CHANGES = f.read()
except IOError:
    README = CHANGES = ''

install_requires=[
    'setuptools',
    'pyramid >= 1.5',
    'WebOb >= 1.3.1', # request.domain and CookieProfile
    'zope.interface',
    ]

tests_require = [
    'WebTest >= 1.3.1', # py3 compat
    ]

docs_extras = [
    'Sphinx',
    'docutils',
    'repoze.sphinx.autointerface',
    ]

testing_extras = tests_require + [
    'nose',
    'coverage',
    'virtualenv', # for scaffolding tests
    ]

setup(name='pyramid_pluggable_session',
      version='0.0.0a2',
      description='A pluggable session implementation for Pyramid',
      long_description=README + '\n\n' +  CHANGES,
      classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI",
        "License :: OSI Approved :: BSD License",
        ],
      keywords='pyramid',
      author="Bert JW Regeer",
      author_email="bertjw@regeer.org",
      url="http://github.com/usingnamespace/pyramid_pluggable_session",
      license="BSD",
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires = install_requires,
      extras_require = {
          'testing':testing_extras,
          'docs':docs_extras,
          },
      tests_require = tests_require,
      test_suite="pyramid_pluggable_session.tests",
      #entry_points =
      )

