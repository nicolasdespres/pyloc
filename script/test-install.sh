#!/bin/bash
#
#::BEGIN::
# USAGE
#
#  test-install.sh <pyenv-version> <index-url> <package-version> <env-dir>
#
# DESCRIPTION
#
#  Install pyloc package in a temporary virtual environment, run
#  `pyloc --version` and exit.
#
#  <pyenv-version>
#   The pyenv version to use.
#
#  <index-url>
#   For testpypi: https://testpypi.python.org/pypi
#   For pypi: https://pypi.python.org/simple
#
#  <package-version>
#   The version of the pyloc package to test.
#
#  <env-dir>
#   A directory where to test the install (WARNING: this directory will be
#   removed).
#
# Copyright (c) 2016, Nicolas Despres
# Report any problem to <nicolas.despres@gmail.com>
#::END::
#

set -o errexit
set -o nounset

export LC_ALL=C
unset CDPATH

# Print the message in the header of this file.
usage()
{
  sed -ne '/^#::BEGIN::/,/^#::END::/p' < "$0" \
    | sed -e '/^#::BEGIN::/d;/^#::END::/d' \
    | sed -e 's/^# //; s/^#//'
}

if [ $# -ne 4 ]
then
  usage
  exit 1
fi
export PYENV_VERSION="$1"
INDEX_URL="$2"
PKG_VERSION="$3"
ENV_DIR="$4"
if grep -q "^3\." <<< $PYENV_VERSION
then
  VTAG=3
else
  VTAG=2
fi

rm -rf "$ENV_DIR"
export VIRTUAL_ENV_DISABLE_PROMPT=x
virtualenv "$ENV_DIR"
cd "$ENV_DIR"
source bin/activate
set -x
pip install --index-url "$INDEX_URL" --ignore-installed "pyloc==$PKG_VERSION"
pyloc --version
pyloc$VTAG --version
set +x
deactivate
cd ..
rm -rf "$ENV_DIR"
