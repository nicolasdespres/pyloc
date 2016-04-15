#!/bin/bash
#
#::BEGIN::
# USAGE
#
#  dev-instal.sh
#
# DESCRIPTION
#
#  Install pyloc in developer mode.
#
# Copyright (c) 2016, Nicolas Despres
# Report any problem to <nicolas.despres@gmail.com>
#::END::
#

set -o errexit
set -o nounset

export LC_ALL=C
unset CDPATH

python setup.py develop
python3 setup.py develop
cat <<EOF
--------------------------------------
If you use pyenv run `pyenv rehash`.
If you use zsh run `rehash`.
WARNING: `pyloc2` driver is not available; only `pyloc` and `pyloc3`.
EOF
