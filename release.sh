#!/bin/bash
#
#::BEGIN::
# USAGE
#
#  release.sh [options] <version>
#
# DESCRIPTION
#
#  Tag the given <version>, create a distribution tarball, check it and
#  release it on pypi.
#
# OPTIONS
#
#
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

# ========= #
# Functions #
# ========= #

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
    echo "Cleaning up release procedure..."
  fi
  rm -rf \
     "VERSION.txt"
}

remove_tag()
{
  git tag -d v$VERSION 2>/dev/null || true
}

# Called when the script exit.
on_exit()
{
  cleanup
}

# Called when the script is interrupt with SIGINT.
on_interrupt()
{
  echo "Release script has been interrupted!!!"
  remove_tag
  exit 2
}

# Check whether $1 is an absolute path name.
is_absolute()
{
  test -z "${1##/*}"
}

check_version_format()
{
  grep -q -E '^[0-9]+\.[0-9]+\.[0-9]+$'
}

# ========================== #
# Parse command line options #
# ========================== #

if [ $# -lt 1 ]
then
  usage
  exit 1
fi

NO_PUSH=false
NO_UPLOAD=false
NO_TEST=false
NO_DISTCHECK=false
PYPI_REPO=pypi
TAG_MSG_FILE=
while [ $# -gt 0 ]
do
  arg="$1"
  case "$arg" in
    --no-push) NO_PUSH=true;;
    --no-upload) NO_UPLOAD=true;;
    --no-test) NO_TEST=true;;
    --no-distcheck) NO_DISTCHECK=true;;
    --repo=*) PYPI_REPO=$(sed -e 's/^--repo=//' <<< "$arg");;
    --tag-msg=*) TAG_MSG_FILE=$(sed -e 's/^--tag-msg=//' <<< "$arg");;
    -h|--help) usage; exit 1;;
    -*) fatal "unknown option '$arg'";;
    *) break;;
  esac
  shift
done

VERSION="$1"
check_version_format <<< "$VERSION" || fatal "invalid version format '$VERSION'"

# ======================= #
# Main script entry point #
# ======================= #

### Move to repository root directory
if is_absolute "$0"
then
  ME="$0"
else
  ME="$PWD/$0"
fi
ME_DIR=$(dirname "$ME")
cd "$ME_DIR"

### Check current working directory
test -d .git || fatal "not run from repository root directory"

### Check branch
CURRENT_BRANCH=$(git branch --no-color | sed -ne '/^\* */s///p')
test "$CURRENT_BRANCH" = "master" || fatal "not on master branch"

### Run test
if ! $NO_TEST
then
  ./runtest.sh 2>&1 | sed -e 's/^/runtest.sh: /'
fi

### Cleanup release/build directories
trap -- on_exit EXIT
trap -- on_interrupt INT
cleanup
rm -rf dist build pyloc.egg-info

### Tag repository
remove_tag
GIT_TAG_ARGS="-a"
test -n "$TAG_MSG_FILE" && GIT_TAG_ARGS="$GIT_TAG_ARGS -F $TAG_MSG_FILE"
git tag $GIT_TAG_ARGS v$VERSION master

### Generate and check version
GIT_VERSION=$(git describe --dirty --always --match 'v*' | sed -e 's/^v//')
echo "$GIT_VERSION" > VERSION.txt
check_version_format <<< "$GIT_VERSION" \
  || fatal "invalid version '$GIT_VERSION'"

### Build distribution
python setup.py sdist
python setup.py bdist_wheel --universal

### Test distribution
if ! $NO_DISTCHECK
then
  ./distcheck.sh "$ME_DIR/dist/pyloc-$VERSION.tar.gz" 2>&1 \
    | sed -e 's/^/distcheck.sh: /'
fi

### Push
if ! $NO_PUSH
then
  git push --follow-tags origin master
fi

### Upload
if ! $NO_UPLOAD
then
  twine upload -r $PYPI_REPO dist/*
fi
