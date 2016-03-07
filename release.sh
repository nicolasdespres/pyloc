#!/bin/bash
#
#::BEGIN::
# USAGE
#
#  release.sh [options] [version]
#
# DESCRIPTION
#
#  Tag the given <version>, create a distribution tarball, check it and
#  release it on pypi. If <version> is not provided no tag are created
#  and a post-release is packaged.
#
# OPTIONS
#
#  --no-master
#   Do not check whether we are on the master branch. Imply --no-push and
#   --no-upload
#
#  --no-push
#   Do not push tags and local commit to origin. Imply --no-upload.
#
#  --no-upload
#   Do not upload release file to the remote repository set by --repo.
#
#  --no-test
#   Do not run test suite as a prelude.
#
#  --no-distcheck
#   Do not run distcheck script for release archive.
#
#  --repo=<reponame>
#   Set the pypi repository to use. Must match one of the index servers
#   listed in your ~/.pypirc file. Typically, this is either 'pypi' or
#   'pypitest'. Default is 'pypi'.
#
#  --tag-msg=<message_filename>
#   Use the message contained in <message_filename> as tag message.
#
#  -h|--help
#   Print this message.
#
# Copyright (c) 2015-2016, Nicolas Desprès
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
}

remove_tag()
{
  if [ -n $VERSION ]
  then
    git tag -d v$VERSION 2>/dev/null || true
  fi
}

# Called when the script exit.
on_exit()
{
  if [ $? -ne 0 ]
  then
    remove_tag
  fi
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
  grep -q -E '^[0-9]+\.[0-9]+\.[0-9]+(rc[0-9]+)?$'
}

log()
{
  echo ">>>>>> "
  echo ">>>>>> " "$@"
  echo ">>>>>> "
}

indirect()
{
  local varname="$1"
  eval echo "\$$varname"
}

# ========================== #
# Parse command line options #
# ========================== #

NO_PUSH=false
NO_UPLOAD=false
NO_TEST=false
NO_DISTCHECK=false
PYPI_REPO=pypi
NO_MASTER=false
TAG_MSG_FILE=
while [ $# -gt 0 ]
do
  arg="$1"
  case "$arg" in
    --no-master) NO_MASTER=true; NO_PUSH=true, NO_UPLOAD=true;;
    --no-push) NO_PUSH=true; NO_UPLOAD=true;;
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

if [ $# -eq 0 ]
then
  VERSION=""
elif [ $# -eq 1 ]
then
  VERSION="$1"
  check_version_format <<< "$VERSION" \
    || fatal "invalid version format '$VERSION'"
else
  usage
  exit 1
fi

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
SCRIPT_DIR="$ME_DIR/script"
DIST_DIR="$ME_DIR/dist"
cd "$ME_DIR"

### Check current working directory
test -d .git || fatal "not run from repository root directory"

### Check branch
if ! $NO_MASTER
then
  CURRENT_BRANCH=$(git branch --no-color | sed -ne '/^\* */s///p')
  test "$CURRENT_BRANCH" = "master" || fatal "not on master branch"
fi

### Cleanup release/build directories
trap -- on_exit EXIT
trap -- on_interrupt INT
cleanup
rm -rf dist build pyloc.egg-info

### Tag repository
remove_tag
if [ -n "$VERSION" ]
then
  GIT_TAG_ARGS="-a"
  test -n "$TAG_MSG_FILE" && GIT_TAG_ARGS="$GIT_TAG_ARGS -F $TAG_MSG_FILE"
  log "Tagging $VERSION"
  git tag $GIT_TAG_ARGS v$VERSION HEAD
fi

### Get version
GIT_VERSION=$(python setup.py --version 2>/dev/null)
log "Release version is: ${GIT_VERSION}"

### Build distribution
log "Creating source distribution"
python setup.py sdist --formats zip,gztar
log "Creating python2 binary distribution"
python setup.py bdist_wheel
log "Creating python3 binary distribution"
python3 setup.py bdist_wheel

### List distribution files
SDIST_PKGS=$(find "$DIST_DIR" -type f \
                  -name "pyloc-${GIT_VERSION}.tar.gz" \
                  -o -name "pyloc-${GIT_VERSION}.zip")
WHEEL2_PKGS=$(find "$DIST_DIR" -type f -name "pyloc-${GIT_VERSION}-py2-*.whl")
WHEEL3_PKGS=$(find "$DIST_DIR" -type f -name "pyloc-${GIT_VERSION}-py3-*.whl")

### List relevant tox environments for each package.
SDIST_ENVS='ALL'
WHEEL2_ENVS=$(tox --listenvs | grep '^py2' | tr '\n' ',')
WHEEL3_ENVS=$(tox --listenvs | grep '^py3' | tr '\n' ',')

### Test distribution
if ! $NO_DISTCHECK
then
  pip install --upgrade tox
  for pkg_list in SDIST WHEEL2 WHEEL3
  do
    for pkg in $(indirect "${pkg_list}_PKGS")
    do
      envs=$(indirect "${pkg_list}_ENVS")
      log "Checking package '$pkg' against environment '$envs'"
      tox_opts=''
      $NO_TEST && tox_opts="$tox_opts --notest"
      [ $envs != 'ALL' ] && tox_opts="$tox_opts -e $envs"
      tox $tox_opts --installpkg "$pkg"
    done
  done
fi

### Check working copy is not dirty.
test -z "$(git status --porcelain 2>/dev/null)" \
  || fatal "working copy is dirty"

### Check that this version is not already used.
if [ -n "$VERSION" ]
then
  git ls-remote --exit-code --tags origin refs/tags/v$VERSION >/dev/null \
    && fatal "version $VERSION already released"
fi

### Push
if ! $NO_PUSH
then
  git push --follow-tags origin master
fi

### Upload
if ! $NO_UPLOAD
then
  pip install --upgrade twine
  # We use twine to upload because it uses an encrypted connection
  # protecting the username/password whereas setuptools do not.
  twine upload -r $PYPI_REPO $DIST_TARBALLS
fi
