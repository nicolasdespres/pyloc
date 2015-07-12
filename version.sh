#!/bin/bash
#
#::BEGIN::
# USAGE
#
#  version.sh
#
# DESCRIPTION
#
#  Compute current version of the project.
#
# Copyright (c) 2015, Nicolas Despres
# Report any problem to <nicolas.despres@gmail.com>
#::END::
#

set -o errexit
set -o nounset

export LC_ALL=C
unset CDPATH

git describe --dirty --always --match 'v*' | sed -e 's/^v//'
