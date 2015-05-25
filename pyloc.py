# -*- encoding: utf-8 -*-
"""Prints the location of the definition a any python object in your file-system.
"""


from __future__ import print_function
import sys
import argparse
import importlib
import inspect
import re
import os
from textwrap import dedent
import ast
from collections import namedtuple


class PylocError(Exception):
    """Base class of all exception raised by this module."""

class ModuleNameError(PylocError):

    def __init__(self, name, error):
        self.name = name
        self.error = error

    def __str__(self):
        return "failed to import '{}' ({}: {})"\
            .format(self.name,
                    type(self.error).__name__,
                    self.error)

class AttributeNameError(PylocError):

    def __init__(self, prefix, name):
        self.prefix = prefix
        self.name = name

    def __str__(self):
        return "cannot get attribute '%s' from '%s'" %(self.name, self.prefix)

Location = namedtuple('Location', 'filename line column')

class _ClassDefVisitor(ast.NodeVisitor):

    def __init__(self, qualname):
        self.qualname = qualname
        self.candidates = []
        self.path = []

    def visit_ClassDef(self, node):
        self.path.append(node)
        qualname = ".".join(n.name for n in self.path)
        if qualname == self.qualname:
            self.candidates.append(node)
        retval = self.generic_visit(node)
        self.path.pop()
        return retval

def _get_file_content(filename):
    with open(filename) as f:
        return f.read()

def _search_classdef(filename, qualname):
    source = _get_file_content(filename)
    root_node = ast.parse(source, filename)
    visitor = _ClassDefVisitor(qualname)
    visitor.visit(root_node)
    return visitor.candidates

def _iter_class_methods(obj):
    for attr in dir(obj):
        val = getattr(obj, attr)
        if inspect.isfunction(val) or inspect.ismethod(val):
            yield val

def _get_line(obj):
    if inspect.ismethod(obj):
        obj = obj.__func__
    if inspect.isfunction(obj):
        obj = obj.__code__
    if inspect.istraceback(obj):
        obj = obj.tb_frame
    if inspect.isframe(obj):
        obj = obj.f_code
    if inspect.iscode(obj) and hasattr(obj, 'co_firstlineno'):
        return obj.co_firstlineno
    return None

def _disamb_class_loc(candidates, obj):
    methods = list(_iter_class_methods(obj))
    if not methods:
        return
    meth_line = min(_get_line(m) for m in methods)
    best_candidate = None
    best_dist = None
    # Select the closest candidates coming before the first method definition
    for c in candidates:
        if c.lineno < meth_line: # Must come before
            dist = meth_line - c.lineno
            if best_dist is None or best_dist > dist:
                best_dist = dist
                best_candidate = c
    return best_candidate

def pyloc(target):
    """Return (filename, lineno) defining object named "module[:qualname]".

    `lineno` may be None if not applicable (i.e. for module or package) or
    if cannot be found.

    Inspired by 'inspect._main()' and 'inspect.findsource()' by
      Ka-Ping Yee <ping@lfw.org> and
      Yury Selivanov <yselivanov@sprymix.com>
    """
    if not target:
        raise ValueError("target must be a non-empty string")
    mod_name, has_qualname, qualname = target.partition(":")
    ### Try to import the module containing the given target.
    try:
        obj = module = importlib.import_module(mod_name)
    except ImportError as exc:
        raise ModuleNameError(mod_name, exc)
    ### Get the object in module
    if has_qualname:
        attrs = qualname.split(".")
        for i in range(len(attrs)):
            attr = attrs[i]
            try:
                new_obj = getattr(obj, attr)
            except AttributeError:
                raise AttributeNameError(".".join([module.__name__]+attrs[:i]),
                                         attr)
            else:
                # If new_obj is not a class, method or function, we won't be
                # able to get the file defining it so we stick stop at the
                # previous object. It may happens when target is a constant.
                if inspect.isclass(new_obj) \
                   or inspect.ismethod(new_obj) \
                   or inspect.isfunction(new_obj):
                    obj = new_obj
                else:
                    break
    ### Get location
    filename = inspect.getsourcefile(obj)
    if not filename:
        return [Location(inspect.getfile(obj), None, None)]
    if inspect.ismodule(obj):
        return [Location(filename, None, None)]
    if inspect.isclass(obj):
        assert has_qualname
        # make some effort to find the best matching class definition:
        # use the one with the least indentation, which is the one
        # that's most probably not inside a function definition.
        candidates = _search_classdef(filename, qualname)
        if candidates:
            if len(candidates) > 1:
                # Try to disambiguite by locating the method defined in the
                # class.
                candidate = _disamb_class_loc(candidates, obj)
                if candidate is not None:
                    return [Location(filename,
                                     candidate.lineno,
                                     candidate.col_offset)]
            return sorted([Location(filename, c.lineno, c.col_offset)
                           for c in candidates])
        return [Location(filename, None, None)]
    return [Location(filename, _get_line(obj), None)]

# =============================== #
# Command line interface function #
# =============================== #

DEFAULT_LOC_FORMAT = "emacs"

def format_loc(loc, format=DEFAULT_LOC_FORMAT):
    if format == 'emacs' or format == 'vi':
        s = ""
        if loc.line:
            s += "+%d" %(loc.line,)
            if loc.column:
                s += ":%d " %(loc.column,)
            else:
                s += " "
        s += loc.filename
        return s
    elif format == 'human':
        s = "Filename: %s" %(filename,)
        if loc.line:
            s += "\nLine: %d" %(loc.line,)
        if loc.column:
            s += "\nColumn: %d" %(loc.column,)
        return s
    else:
        raise ValueError("unsupported format: {}".format(format))

_EPILOGUE = """
environment variables:
 PYLOC_DEFAULT_FORMAT - default output format (default: {default_format})

Copyright (c) 2015, Nicolas Despres
All right reserved.
""".format(
    default_format=DEFAULT_LOC_FORMAT,
    )

def build_cli():
    class RawDescriptionWithArgumentDefaultsHelpFormatter(
            argparse.ArgumentDefaultsHelpFormatter,
            argparse.RawDescriptionHelpFormatter,
    ):
        """Mix both formatter."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=dedent(_EPILOGUE),
        formatter_class=RawDescriptionWithArgumentDefaultsHelpFormatter)
    parser.add_argument(
        "-f", "--format",
        action="store",
        choices=("emacs", "vi", "human"),
        default=os.environ.get("PYLOC_DEFAULT_FORMAT", DEFAULT_LOC_FORMAT),
        help="How to write object location")
    parser.add_argument(
        "-a", "--all",
        action="store_true",
        help="Print all possible location in case ambiguities")
    parser.add_argument(
        "object_name",
        action="store",
        help="A python object named: module[:qualname]")
    return parser

def main(argv):
    cli = build_cli()
    options = cli.parse_args(argv[1:])
    try:
        locs = pyloc(options.object_name)
    except PylocError as e:
        sys.stderr.write("pyloc: ")
        sys.stderr.write(str(e))
        sys.stderr.write("\n")
        return 1
    else:
        if options.all:
            locs_to_print = locs
        else:
            locs_to_print = [locs[0]]
        for loc in locs:
            sys.stdout.write(format_loc(loc, format=options.format))
            sys.stdout.write("\n")
        return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
