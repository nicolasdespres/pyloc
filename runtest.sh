#!/bin/bash
#
#::BEGIN::
# USAGE
#
#  runtest.sh
#
# DESCRIPTION
#
#  Run test suite against several version of python. This script is called
#  by the release script.
#
# Copyright (c) 2015, Nicolas Despres
# Report any problem to <nicolas.despres@gmail.com>
#::END::
#

set -o errexit
set -o nounset

export LC_ALL=C
unset CDPATH


# ======================= #
# Script main entry point #
# ======================= #

for version in 2.7.10 3.2.3 3.2.6 3.3.6 3.4.3 3.5.1
do
  PYENV_VERSION=$version python -m unittest test_pyloc
done
