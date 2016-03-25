# -*- encoding: utf-8 -*-
# Copyright (c) 2015-2016, Nicolas Desprès

# Relevant documentation used when writing this file:
#   https://docs.python.org/3/library/distutils.html
#   http://www.diveinto.org/python3/packaging.html
#   http://www.scotttorborg.com/python-packaging/
# and of course several example projects such as: csvkit, nose or buildout.

from setuptools import setup
from setuptools.command.sdist import sdist
from wheel.bdist_wheel import bdist_wheel

import os
import sys
import subprocess
import errno
import codecs
from contextlib import contextmanager

ROOT_DIR = os.path.dirname(__file__)
VERSION_TXT = os.path.join(ROOT_DIR, "VERSION.txt")
REVISION_TXT = os.path.join(ROOT_DIR, "REVISION.txt")
README_RST = os.path.join(ROOT_DIR, "README.rst")
VERSION_SCRIPT = os.path.join("script", "version")

def readfile(filepath):
    with codecs.open(filepath,
                     mode="r",
                     encoding="utf-8") as stream:
        return stream.read()

def writefile(filepath, content):
    with codecs.open(filepath, mode="w", encoding="utf-8") as stream:
        stream.write(content)

def get_version():
    try:
        return readfile(VERSION_TXT).strip()
    except IOError as e:
        if e.errno == errno.ENOENT:
            cmd = [VERSION_SCRIPT, "get", "--no-dirty"]
            return subprocess.check_output(cmd).decode().strip()

def get_revision():
    try:
        return readfile(REVISION_TXT).strip()
    except IOError as e:
        if e.errno == errno.ENOENT:
            cmd = [VERSION_SCRIPT, "revision"]
            return subprocess.check_output(cmd).decode().strip()

def is_git_dir(dirpath=None):
    if dirpath is None:
        dirpath = os.getcwd()
    cmd = ["git", "-C", str(dirpath), "rev-parse", "--git-dir"]
    try:
        with open(os.devnull, "wb") as devnull:
            subprocess.check_call(cmd, stdout=devnull, stderr=devnull)
    except subprocess.CalledProcessError:
        return False
    return True

def git_file_is_modified(filepath):
    cmd = ["git", "status", "--porcelain", str(filepath)]
    output = subprocess.check_output(cmd).decode()
    return output != u''

def sed_i(script, *filepaths):
    cmd = [ "sed", "-i", '', "-e", script ] + list(filepaths)
    subprocess.check_call(cmd)

def rm_f(path):
    try:
        os.unlink(path)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise e

@contextmanager
def inject_version_info():
    pyloc_py = "pyloc.py"
    if not is_git_dir():
        yield
        return
    if git_file_is_modified(pyloc_py):
        raise RuntimeError("'%s' has un-commited changes"%(pyloc_py,))
    try:
        print("inject version number into module")
        VERSION = get_version()
        sed_i(
            "s/^__version__ = 'dev'$/__version__ = '%s'/"%(VERSION,),
            pyloc_py)
        writefile(VERSION_TXT, VERSION)
        print("inject revision number into module")
        REVISION = get_revision()
        writefile(REVISION_TXT, REVISION)
        sed_i(
            "s/^__revision__ = 'git'$/__revision__ = '%s'/"%(REVISION,),
            pyloc_py)
        yield
    finally:
        print("restore %s"%(pyloc_py,))
        subprocess.check_call(["git", "checkout", pyloc_py])
        print("remove %s"%(VERSION_TXT,))
        rm_f(VERSION_TXT)
        print("remove %s"%(REVISION_TXT,))
        rm_f(REVISION_TXT)

class SDistProxy(sdist):
    """Hook sdist command"""

    def run(self):
        with inject_version_info():
            # Super class is an old-style class, so we use old-style
            # "super" call.
            sdist.run(self)

class BDistWheelProxy(bdist_wheel):

    def run(self):
        with inject_version_info():
            # Super class is an old-style class, so we use old-style
            # "super" call.
            bdist_wheel.run(self)

PY_VERSION_SUFFIX = '%s' % (sys.version_info.major,)

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
    long_description=readfile(README_RST),
    author="Nicolas Despres",
    author_email='nicolas.despres@gmail.com',
    license="Simplified BSD",
    keywords='utility',
    url='https://github.com/nicolasdespres/pyloc',
    platforms=["any"],
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
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
    ],
    cmdclass={
        'sdist': SDistProxy,
        'bdist_wheel': BDistWheelProxy,
    },
)
