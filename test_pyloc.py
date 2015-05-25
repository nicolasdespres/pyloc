# -*- encoding: utf-8 -*-
"""Test 'pyloc' module.
"""


import unittest
import sysconfig
import sys
import os
import contextlib
import re
import textwrap
import tempfile
import shutil

from pyloc import pyloc
from pyloc import ModuleNameError
from pyloc import AttributeNameError


# Guidelines:
# - Generate the package/module fixture for testing.
# - If you cannot, use only fixture names that are part of the standard
#   library for all supported version of Python and that are not imported
#   by either this module and pyloc.


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

def gen_fixture_in(spec, dirpath):
    for k in spec:
        v = spec[k]
        subpath = os.path.join(dirpath, k)
        if isinstance(v, dict):
            os.mkdir(subpath)
            with open(os.path.join(subpath, "__init__.py"), "w") as stream:
                stream.write("# -*- encoding: utf-8 -*-\n")
                stream.write("\"\"\"generated package\n\"\"\"")
            gen_fixture_in(v, subpath)
        else:
            with open(subpath+".py", "w") as stream:
                stream.write(v)

@contextlib.contextmanager
def make_tmpdir(*args, **kwargs):
    """Make temporary directory.

    Needed because tempfile.TemporaryDirectory is Python3 only.
    """
    try:
        tmpdir = tempfile.mkdtemp(*args, **kwargs)
        yield tmpdir
    finally:
        shutil.rmtree(tmpdir)

class FixtureCtxt(object):

    def __init__(self, testcase, tmpdir):
        self.testcase = testcase
        self.tmpdir = tmpdir

    def assertLocEqual(self, *args, **kwargs):
        self.testcase.assertLocEqual(self.tmpdir, *args, **kwargs)

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

    def assertLocEqual(self, rootdir, expected, modname, qualname=None,
                       locs=None):
        self.assertFalse(modname in sys.modules,
                         "'%s' is already imported" % (modname,))
        fullname = modname
        if qualname:
            fullname += ":" + qualname
        if not os.path.isabs(expected):
            expected = os.path.join(rootdir, expected)
        if locs is None:
            locs = [(None, None)]
        elif isinstance(locs, tuple):
            locs = [locs]
        elif isinstance(locs, int):
            locs = [(locs, None)]
        with save_sys_modules():
            actuals = pyloc(fullname)
        self.assertEqual(len(locs), len(actuals))
        for actual, loc in zip(actuals, locs):
            self.assertEqual(expected, actual.filename)
            self.assertEqual(loc[0], actual.line)
            self.assertEqual(loc[1], actual.column)

    @contextlib.contextmanager
    def fixture(self, spec):
        with make_tmpdir() as tmpdir, \
             save_sys_modules():
            sys.path.insert(0, tmpdir)
            gen_fixture_in(spec, tmpdir)
            yield FixtureCtxt(self, tmpdir)

    def test_module_name_error(self):
        with self.assertRaises(ModuleNameError):
            pyloc("list")

    def test_report_exception_raised_from_imported_module(self):
        modcontent = textwrap.dedent(
            """\
            raise RuntimeError("intentional error")
            """)
        with self.fixture({"pyloc_mymod":modcontent}):
            with self.assertRaises(RuntimeError) as cm:
                pyloc("pyloc_mymod")
            self.assertRegexp(str(cm.exception), "intentional error")

    def test_attribute_name_error(self):
        with self.assertRaises(AttributeNameError) as cm:
            pyloc("subprocess:doesnotexist")
        self.assertRegexp(str(cm.exception),
                          r"'doesnotexist'.+'subprocess'")

    def test_sub_attribute_name_error(self):
        with self.assertRaises(AttributeNameError) as cm:
            pyloc("subprocess:Popen.doesnotexist")
        self.assertRegexp(str(cm.exception),
                          r"'doesnotexist'.+'subprocess.Popen'")


    def test_package(self):
        spec = {"pyloc_testpkg":{"utils":"def func(): pass"}}
        with self.fixture(spec) as fctxt:
            fctxt.assertLocEqual("pyloc_testpkg/__init__.py", "pyloc_testpkg")

    def test_no_source_file(self):
        filename = os.path.join(sysconfig.get_config_var("DESTSHARED"),
                                "mmap.so")
        self.assertLocEqual(PLATSTDLIB_PATH, filename, "mmap")

    def test_module(self):
        with self.fixture({"pyloc_testmod":""}) as fctxt:
            fctxt.assertLocEqual("pyloc_testmod.py", "pyloc_testmod")

    def test_module_in_package(self):
        spec = {"pyloc_testpkg":{"utils":""}}
        with self.fixture(spec) as fctxt:
            fctxt.assertLocEqual("pyloc_testpkg/utils.py",
                                 "pyloc_testpkg.utils")

    def test_module_in_module(self):
        spec = {"pyloc_testmod":"import sys"}
        with self.fixture(spec) as fctxt:
            fctxt.assertLocEqual("pyloc_testmod.py",
                                 "pyloc_testmod", qualname="sys")

    def test_module_in_class(self):
        modcontent = textwrap.dedent(
            """\
            class C(object):
                import sys
            """)
        spec = {"pyloc_testmod":modcontent}
        with self.fixture(spec) as fctxt:
            fctxt.assertLocEqual("pyloc_testmod.py",
                                 "pyloc_testmod", qualname="C.sys",
                                 locs=(1,0))

    def test_function_in_module_in_package(self):
        spec = {"pyloc_testpkg":{"utils":"def func(): pass"}}
        with self.fixture(spec) as fctxt:
            fctxt.assertLocEqual("pyloc_testpkg/utils.py",
                                 "pyloc_testpkg.utils",
                                 qualname="func",
                                 locs=1)

    def test_function_in_module(self):
        spec = {"pyloc_testmod":"def func(): pass"}
        with self.fixture(spec) as fctxt:
            fctxt.assertLocEqual("pyloc_testmod.py", "pyloc_testmod",
                                 qualname="func",
                                 locs=1)

    def test_multiple_functions(self):
        for cond, loc in ((True, 3), (False, 6)):
            modcontent = textwrap.dedent(
                """\
                cond = {cond}
                if cond:
                    def f():
                        pass
                else:
                    def f():
                        pass
                """.format(cond=cond))
            spec = {"pyloc_testmod":modcontent}
            with self.fixture(spec) as fctxt:
                fctxt.assertLocEqual("pyloc_testmod.py", "pyloc_testmod",
                                     qualname="f",
                                     locs=loc)

    def test_follow_aliases(self):
        modcontent = textwrap.dedent(
            """\
            def realf():
                pass
            f = realf
            """)
        spec = {"pyloc_testmod":modcontent}
        with self.fixture(spec) as fctxt:
            fctxt.assertLocEqual("pyloc_testmod.py", "pyloc_testmod",
                                 qualname="f",
                                 locs=1)

    def test_closure(self):
        modcontent = textwrap.dedent(
            """\
            def realf():
                def f():
                    pass
                return f
            func = realf()
            """)
        spec = {"pyloc_testmod":modcontent}
        with self.fixture(spec) as fctxt:
            fctxt.assertLocEqual("pyloc_testmod.py", "pyloc_testmod",
                                 qualname="func",
                                 locs=2)

    def test_setattr(self):
        modcontent = textwrap.dedent(
            """\
            import sys
            def realf():
                def f():
                    pass
                return f
            this_module = sys.modules[__name__]
            setattr(this_module, "func", realf())
            """)
        spec = {"pyloc_testmod":modcontent}
        with self.fixture(spec) as fctxt:
            fctxt.assertLocEqual("pyloc_testmod.py", "pyloc_testmod",
                                 qualname="func",
                                 locs=3)

    def test_class(self):
        spec = {"pyloc_testmod":"class Foo(object): pass"}
        with self.fixture(spec) as fctxt:
            fctxt.assertLocEqual("pyloc_testmod.py", "pyloc_testmod",
                                 qualname="Foo",
                                 locs=(1, 0))

    def test_multiple_classes(self):
        for cond in (True, False):
            modcontent = textwrap.dedent(
                """\
                cond = {cond}
                if cond:
                    class C(object):
                        pass
                else:
                    class C(object):
                        pass
                """.format(cond=cond))
            spec = {"pyloc_testmod":modcontent}
            with self.fixture(spec) as fctxt:
                fctxt.assertLocEqual("pyloc_testmod.py", "pyloc_testmod",
                                     qualname="C",
                                     locs=[(3, 4), (6, 4)])

    def test_multiple_classes_disamb(self):
        for cond, loc in ((True, (3, 4)), (False, (7, 4))):
            modcontent = textwrap.dedent(
                """\
                cond = {cond}
                if cond:
                    class C(object):
                        def m():
                            pass
                else:
                    class C(object):
                        def m():
                            pass
                """.format(cond=cond))
            spec = {"pyloc_testmod":modcontent}
            with self.fixture(spec) as fctxt:
                fctxt.assertLocEqual("pyloc_testmod.py", "pyloc_testmod",
                                     qualname="C",
                                     locs=loc)

    def test_class_robust_comment(self):
        modcontent = textwrap.dedent(
            """\
            # -*- encoding: utf-8 -*-
            # This module defines the class called Foo:
            #
            # class Foo()
            #

            class Foo(object):
                pass
            """)
        spec = {"pyloc_testmod":modcontent}
        with self.fixture(spec) as fctxt:
            fctxt.assertLocEqual("pyloc_testmod.py", "pyloc_testmod",
                                 qualname="Foo",
                                 locs=(7, 0))

    def test_class_robust_docstring(self):
        modcontent = textwrap.dedent(
            """\
            # -*- encoding: utf-8 -*-
            \"\"\"
            This module defines the class called Foo:

            class Foo()
            \"\"\"

            class Foo(object):
                pass
            """)
        spec = {"pyloc_testmod":modcontent}
        with self.fixture(spec) as fctxt:
            fctxt.assertLocEqual("pyloc_testmod.py", "pyloc_testmod",
                                 qualname="Foo",
                                 locs=(8, 0))

    def test_nested_class(self):
        modcontent = textwrap.dedent(
            """\
            # -*- encoding: utf-8 -*-
            class Foo(object):
                class Foo(object):
                    class Foo(object):
                        pass
            """)
        spec = {"pyloc_testmod":modcontent}
        with self.fixture(spec) as fctxt:
            fctxt.assertLocEqual("pyloc_testmod.py", "pyloc_testmod",
                                 qualname="Foo.Foo.Foo",
                                 locs=(4, 8))

    def test_class_namedtuple(self):
        modcontent = textwrap.dedent(
            """\
            from collections import namedtuple
            Point = namedtuple("Point", "x y")
            """)
        spec = {"pyloc_testmod":modcontent}
        with self.fixture(spec) as fctxt:
            fctxt.assertLocEqual("pyloc_testmod.py", "pyloc_testmod",
                                 qualname="Point",
                                 locs=(2, 0))

    def test_class_nested_namedtuple(self):
        modcontent = textwrap.dedent(
            """\
            from collections import namedtuple
            class C(object):
                Point = namedtuple("Point", "x y")
            Point = C.Point(1, 2)
            def f():
                Point = C.Point(2, 3)
            """)
        spec = {"pyloc_testmod":modcontent}
        with self.fixture(spec) as fctxt:
            fctxt.assertLocEqual("pyloc_testmod.py", "pyloc_testmod",
                                 qualname="C.Point",
                                 locs=(3, 4))

    def test_class_nested_namedtuple(self):
        modcontent = textwrap.dedent(
            """\
            from collections import namedtuple
            class C(object):
                Point = namedtuple("Point", "x y")
            """)
        spec = {"pyloc_testmod":modcontent}
        with self.fixture(spec) as fctxt:
            fctxt.assertLocEqual("pyloc_testmod.py", "pyloc_testmod",
                                 qualname="C.Point",
                                 locs=(3, 4))

    def test_class_alias(self):
        modcontent = textwrap.dedent(
            """\
            def f():
                D = 51
            class C(object):
                D = 42
            D = C
            """)
        spec = {"pyloc_testmod":modcontent}
        with self.fixture(spec) as fctxt:
            fctxt.assertLocEqual("pyloc_testmod.py", "pyloc_testmod",
                                 qualname="D",
                                 locs=(5, 0))

    def test_class_alias_redefinition(self):
        modcontent = textwrap.dedent(
            """\
            class C(object):
                D = 42
            D = 42
            D = C
            """)
        spec = {"pyloc_testmod":modcontent}
        with self.fixture(spec) as fctxt:
            fctxt.assertLocEqual("pyloc_testmod.py", "pyloc_testmod",
                                 qualname="D",
                                 locs=[(3, 0),(4,0)])

    def test_method(self):
        modcontent = textwrap.dedent(
            """\
            class Foo(object):
                def meth(self):
                    pass
            """)
        with self.fixture({"pyloc_testmod":modcontent}) as fctxt:
            fctxt.assertLocEqual("pyloc_testmod.py", "pyloc_testmod",
                                 qualname="Foo.meth",
                                 locs=2)

    def test_nested_method(self):
        modcontent = textwrap.dedent(
            """\
            def meth():
                pass
            class Bar(object):
                def meth(self):
                    pass
            class Foo(object):
                def meth(self):
                    pass
            class A(object):
                class B(object):
                    def meth(self):
                        pass
            """)
        with self.fixture({"pyloc_testmod":modcontent}) as fctxt:
            fctxt.assertLocEqual("pyloc_testmod.py", "pyloc_testmod",
                                 qualname="Foo.meth",
                                 locs=7)
            fctxt.assertLocEqual("pyloc_testmod.py", "pyloc_testmod",
                                 qualname="Bar.meth",
                                 locs=4)
            fctxt.assertLocEqual("pyloc_testmod.py", "pyloc_testmod",
                                 qualname="A.B.meth",
                                 locs=11)
            fctxt.assertLocEqual("pyloc_testmod.py", "pyloc_testmod",
                                 qualname="meth",
                                 locs=1)

    def test_constant(self):
        modcontent = textwrap.dedent(
            """\
            PI = 3.14
            """)
        with self.fixture({"pyloc_testmod":modcontent}) as fctxt:
            fctxt.assertLocEqual("pyloc_testmod.py", "pyloc_testmod",
                                 qualname="PI")

    @unittest.skipIf(PY_VERSION >= (3, 0, 0), "test for python 2 only")
    def test_unicode(self):
        modcontent = textwrap.dedent(
            """\
            PI = 3.14
            """)
        with self.fixture({"pyloc_testmod":modcontent}) as fctxt:
            fctxt.assertLocEqual(unicode("pyloc_testmod.py"),
                                 unicode("pyloc_testmod"),
                                 qualname=unicode("PI"))
