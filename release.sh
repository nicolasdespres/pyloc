#!/bin/bash
#
#::BEGIN::
# USAGE
#
#  release.sh
#
# DESCRIPTION
#
#  Release this project on pypi.
#
# Copyright (c) 2015, Nicolas Despres
# Report any problem to <nicolas.despres@gmail.com>
#::END::
#

set -o errexit
set -o nounset

export LC_ALL=C
unset CDPATH

# ========= #
# Functions #
# ========= #

for version in 2.7.10 3.2.3 3.2.6 3.3.6 3.4.3
do
  PYENV_VERSION=$version python -m unittest test_pyloc
done
rm -rf dist build pyloc.egg-info
python setup.py sdist
python setup.py bdist_wheel --universal
twine upload dist/*
