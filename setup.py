# -*- encoding: utf-8 -*-

# Relevant documentation used when writing this file:
#   https://docs.python.org/3/library/distutils.html
#   http://www.diveinto.org/python3/packaging.html
#   http://www.scotttorborg.com/python-packaging/
# and of course several example projects such as: csvkit, nose or buildout.

from setuptools import setup
import os
import sys
import subprocess

ROOT_DIR = os.path.dirname(__file__)

def read(*rnames):
    with open(os.path.join(ROOT_DIR, *rnames)) as stream:
        return stream.read()

def get_version():
    out = subprocess.check_output(["git","describe","--always","--match","v*"])
    out = out.strip()
    return out[1:]

PY_VERSION_SUFFIX = '-%s.%s' % sys.version_info[:2]

setup(
    name="pyloc",
    version=get_version(),
    # We only have a single module to distribute
    packages=[],
    py_modules=[
        "pyloc",
        "test_pyloc",
    ],
    # We only depends on Python standard library.
    install_requires=[],
    # Generate a command line interface driver.
    entry_points={
        'console_scripts': [
            "pyloc=pyloc:_main",
            "pyloc%s=pyloc:_main" % (PY_VERSION_SUFFIX,),
        ],
    },
    # How to run the test suite.
    test_suite='nose.collector',
    tests_require=['nose'],
    # What it does, who wrote it and where to find it.
    description="Locate python object definition in your file-system",
    long_description=read('README.rst'),
    author="Nicolas Despres",
    author_email='nicolas.despres@gmail.com',
    license="Simplified BSD",
    keywords='utility',
    url='https://github.com/nicolasdespres/pyloc',
    # Pick some from https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
    ],
)
