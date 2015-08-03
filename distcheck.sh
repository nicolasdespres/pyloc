#!/bin/bash
#
#::BEGIN::
# USAGE
#
#  distcheck.sh <version> <revision> <dist_tarball>
#
# DESCRIPTION
#
#  Check that a distribution tarball install and works properly.
#
# Copyright (c) 2015, Nicolas Despres
# Report any problem to <nicolas.despres@gmail.com>
#::END::
#

set -o errexit
set -o errtrace
set -o nounset

export LC_ALL=C
unset CDPATH

# ======================= #
# Configuration variables #
# ======================= #

: ${RELEASE_DEBUG:=false}
: ${DIST_ENV_DIR:="distcheck_env"}

# Print the message in the header of this file.
usage()
{
  sed -ne '/^#::BEGIN::/,/^#::END::/p' < "$0" \
    | sed -e '/^#::BEGIN::/d;/^#::END::/d' \
    | sed -e 's/^# //; s/^#//'
}

# Print its arguments on stderr prefixed by the base name of this script and
# a 'fatal' tag.
fatal()
{
  echo >&2 "fatal: $@"
  exit 1
}

# Clean up before to finish.
cleanup()
{
  if $RELEASE_DEBUG
  then
    echo "You are in debug mode. No directory are removed."
    return
  else
    echo "Cleaning up distcheck..."
  fi
  rm -rf "$DIST_ENV_DIR"
}

# Called when the script exit.
on_exit()
{
  cleanup
}

# Called when the script is interrupt with SIGINT.
on_interrupt()
{
  echo "Distcheck has been interrupted!!!"
  exit 2 # Trigger cleanup called by on_exit.
}

# ========================== #
# Parse command line options #
# ========================== #

if [ $# -ne 3 ]
then
  usage
  exit 1
fi

GIT_VERSION="$1"
GIT_REVISION="$2"
DISTTARBALL="$3"

# ======================= #
# Script main entry point #
# ======================= #

trap -- on_exit EXIT
trap -- on_interrupt INT

echo ">>> Distchecking '$DISTTARBALL'"
cleanup # Cleanup in case previous was killed
if grep -e '-py3-' <<< "$DISTTARBALL"
then
  VENV=pyvenv
  PIP=pip3
  PYTHON=python3
else
  VENV=virtualenv
  PIP=pip
  PYTHON=python
fi
TAG=$($PYTHON -c 'import sys; print("-%s.%s" % sys.version_info[:2])')
### Test distribution
$VENV "$DIST_ENV_DIR"
(
  set +o nounset
  . "$DIST_ENV_DIR/bin/activate"
  set -o nounset
  cd /tmp
  $PIP install "$DISTTARBALL"
  pyloc subprocess
  pyloc$TAG subprocess
  BUILTIN_VERSION=$($PYTHON -c 'import pyloc; print(pyloc.VERSION)')
  test "$BUILTIN_VERSION" = "$GIT_VERSION" \
    || fatal "built-in version '$BUILTIN_VERSION' not equal to git"\
             "version '$GIT_VERSION'"
  BUILTIN_REVISION=$($PYTHON -c 'import pyloc; print(pyloc.REVISION)')
  test "$BUILTIN_REVISION" = "$GIT_REVISION" \
    || fatal "built-ni revision '$BUILTIN_REVISION' not equal to git revision"\
             "'$GIT_REVISION'"
  $PYTHON -m unittest test_pyloc
)
echo "Distcheck successful!!!"
