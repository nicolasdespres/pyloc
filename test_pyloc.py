# -*- encoding: utf-8 -*-
"""Test 'pyloc' module.
"""


import unittest
import sysconfig
import sys
import os
import contextlib
import re

from pyloc import pyloc
from pyloc import ModuleNameError
from pyloc import AttributeNameError


# Guidelines:
# - Use only fixture names that are part of the standard library for all
#   supported version of Python and that are not imported by either this
#   module and pyloc.


PLATSTDLIB_PATH = sysconfig.get_path('platstdlib')
PY_VERSION = tuple(map(int, sysconfig.get_config_var('py_version').split(".")))

@contextlib.contextmanager
def save_sys_modules():
    saved_modules = sys.modules.copy()
    try:
        yield
    finally:
        to_del = []
        for k in sys.modules:
            if k not in saved_modules:
                to_del.append(k)
        for k in to_del:
            del sys.modules[k]

def get_line(filename, lineno):
    with open(filename) as f:
        for i, line in enumerate(f):
            if i + 1 == lineno:
                return line

class TestPyloc(unittest.TestCase):

    # Duplicated from unittest.TestCase because it is named assertRegexpMatches
    # in python 2.7.x
    def assertRegexp(self, text, expected_regex, msg=None):
        if isinstance(expected_regex, (str, bytes)):
            assert expected_regex, "expected_regex must not be empty."
            expected_regex = re.compile(expected_regex)
        if not expected_regex.search(text):
            msg = msg or "Regex didn't match"
            msg = '%s: %r not found in %r' % (msg, expected_regex.pattern, text)
            raise self.failureException(msg)

    def assertLocEqual(self, expected, modname, qualname=None,
                       match_line=None):
        self.assertFalse(modname in sys.modules,
                         "'%s' is already imported" % (modname,))
        fullname = modname
        if qualname:
            fullname += ":" + qualname
        if not os.path.isabs(expected):
            expected = os.path.join(PLATSTDLIB_PATH, expected)
        with save_sys_modules():
            filename, lineno = pyloc(fullname)
        if match_line is not None:
            self.assertIsInstance(lineno, int)
            self.assertIsNotNone(lineno, filename)
            line = get_line(filename, lineno)
            self.assertRegexp(line,
                              r"^\s*{}\s+[_a-zA-Z]+".format(match_line))
        self.assertEqual(expected, filename)

    def test_module_name_error(self):
        with self.assertRaises(ModuleNameError):
            pyloc("list")

    def test_attribute_name_error(self):
        with self.assertRaises(AttributeNameError) as cm:
            with save_sys_modules():
                pyloc("subprocess:doesnotexist")
        self.assertRegexp(str(cm.exception),
                          r"'doesnotexist'.+'subprocess'")

    def test_sub_attribute_name_error(self):
        with self.assertRaises(AttributeNameError) as cm:
            with save_sys_modules():
                pyloc("subprocess:Popen.doesnotexist")
        self.assertRegexp(str(cm.exception),
                          r"'doesnotexist'.+'subprocess.Popen'")


    def test_package(self):
        self.assertLocEqual("email/__init__.py", "email")

    def test_no_source_file(self):
        filename = os.path.join(sysconfig.get_config_var("DESTSHARED"),
                                "zlib.so")
        self.assertLocEqual(filename, "zlib")

    def test_module(self):
        self.assertLocEqual("subprocess.py", "subprocess")

    def test_module_in_package(self):
        self.assertLocEqual("email/utils.py", "email.utils")

    def test_function_in_module_in_package(self):
        self.assertLocEqual("email/utils.py", "email.utils",
                            qualname="formataddr",
                            match_line='def')

    def test_function_in_module(self):
        self.assertLocEqual("subprocess.py", "subprocess",
                            qualname="check_output",
                            match_line='def')

    def test_class(self):
        self.assertLocEqual("subprocess.py", "subprocess",
                            qualname="Popen",
                            match_line='class')

    def test_method(self):
        self.assertLocEqual("subprocess.py", "subprocess",
                            qualname="Popen.wait",
                            match_line='def')

    def test_constant(self):
        self.assertLocEqual("subprocess.py", "subprocess", qualname="PIPE")

    @unittest.skipIf(PY_VERSION >= (3, 0, 0), "test for python 2 only")
    def test_unicode(self):
        self.assertLocEqual(unicode("subprocess.py"),
                            unicode("subprocess"),
                            qualname=unicode("PIPE"))
