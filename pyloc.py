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
    mod_name, has_attrs_name, attrs_name = target.partition(":")
    ### Try to import the module containing the given target.
    try:
        obj = module = importlib.import_module(mod_name)
    except ImportError as exc:
        raise ModuleNameError(mod_name, exc)
    ### Get the object in module
    if has_attrs_name:
        attrs = attrs_name.split(".")
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
        return inspect.getfile(obj), None
    if inspect.ismodule(obj):
        return filename, None
    if inspect.isclass(obj):
        name = obj.__name__
        pat = re.compile(r'^(\s*)class\s*' + name + r'\b')
        # make some effort to find the best matching class definition:
        # use the one with the least indentation, which is the one
        # that's most probably not inside a function definition.
        candidates = []
        with open(filename) as f:
            for i, line in enumerate(f):
                lineno = i + 1
                match = pat.match(line)
                if match:
                    # if it's at toplevel, it's already the best one
                    if line[0] == 'c':
                        return filename, lineno
                    # else add whitespace to candidate list
                    candidates.append((match.group(1), lineno))
        if candidates:
            # this will sort by whitespace, and by line number,
            # less whitespace first
            candidates.sort()
            return filename, candidates[0][1]
        else:
            return filename, None
    if inspect.ismethod(obj):
        obj = obj.__func__
    if inspect.isfunction(obj):
        obj = obj.__code__
    if inspect.istraceback(obj):
        obj = obj.tb_frame
    if inspect.isframe(obj):
        obj = obj.f_code
    if inspect.iscode(obj):
        if not hasattr(obj, 'co_firstlineno'):
            return filename, None
        return filename, obj.co_firstlineno
    return filename, None

# =============================== #
# Command line interface function #
# =============================== #

DEFAULT_LOC_FORMAT = "emacs"

def format_loc(filename, lineno, format=DEFAULT_LOC_FORMAT):
    if format == 'emacs' or format == 'vi':
        s = ""
        if lineno:
            s += "+%d " %(lineno,)
        s += filename
        return s
    elif format == 'human':
        s = "Filename: %s" %(filename,)
        if lineno:
            s += "\nLine: %d" %(lineno,)
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
        "object_name",
        action="store",
        help="A python object named: module[:qualname]")
    return parser

def main(argv):
    cli = build_cli()
    options = cli.parse_args(argv[1:])
    try:
        filename, lineno = pyloc(options.object_name)
    except PylocError as e:
        sys.stderr.write("pyloc: ")
        sys.stderr.write(str(e))
        sys.stderr.write("\n")
        return 1
    else:
        sys.stdout.write(format_loc(filename, lineno, format=options.format))
        sys.stdout.write("\n")
        return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
