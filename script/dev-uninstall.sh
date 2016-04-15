#!/bin/bash
#
#::BEGIN::
# USAGE
#
#  dev-uninstall.sh
#
# DESCRIPTION
#
#  Remove developer mode installation of pyloc.
#
# Copyright (c) 2016, Nicolas Despres
# Report any problem to <nicolas.despres@gmail.com>
#::END::
#

set -o errexit
set -o nounset

export LC_ALL=C
unset CDPATH

python setup.py develop --uninstall
python3 setup.py develop --uninstall
cat <<EOF
--------------------------------------
If you use pyenv run `pyenv rehash`.
If you use zsh run `rehash`.
EOF
