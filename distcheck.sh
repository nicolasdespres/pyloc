#!/bin/bash
#
#::BEGIN::
# USAGE
#
#  distcheck.sh <dist_tarball>
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

if [ $# -ne 1 ]
then
  usage
  exit 1
fi

DISTTARBALL="$1"

# ======================= #
# Script main entry point #
# ======================= #

trap -- on_exit EXIT
trap -- on_interrupt INT

### Cleanup in case previous was killed
cleanup

### Test distribution in python2
virtualenv "$DIST_ENV_DIR"
(
  set +o nounset
  . "$DIST_ENV_DIR/bin/activate"
  set -o nounset
  cd /tmp
  pip install "$DISTTARBALL"
  pyloc subprocess
  python -m unittest test_pyloc
)

### Final cleanup
cleanup
