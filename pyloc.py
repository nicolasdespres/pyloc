# -*- encoding: utf-8 -*-
"""Print the path to the file defining a given python qualified name.
"""


from __future__ import print_function
import sys
import argparse
from importlib import import_module
import os


def subnames(name):
    curname = ""
    names = []
    for n in name.split("."):
        if curname:
            curname += "." + n
        else:
            curname = n
        names.append(curname)
    names.reverse()
    return names

def raw_pyfile(name):
    first_import_err = None
    for n in subnames(name):
        try:
            mod = import_module(n)
        except ImportError as e:
            if first_import_err is None:
                first_import_err = e
        else:
            return mod.__file__
    raise e

def pyc2py(pathname):
    assert pathname.endswith(".pyc")
    return pathname[:-1]

def pyfile(name):
    path = raw_pyfile(name)
    if path.endswith(".pyc"):
        py_path = pyc2py(path)
        if os.path.exists(py_path):
            return py_path
    return path

def build_cli():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        "name",
        action="store",
        help="A python qualified name.")
    return parser

def main(argv):
    cli = build_cli()
    options = cli.parse_args(argv[1:])
    filename = pyfile(options.name)
    if filename:
        print(filename)
        return 0
    else:
        print("pyfile: cannot find definition file for '%s'" % options.name)
        return 1

if __name__ == "__main__":
    sys.exit(main(sys.argv))
