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
set -o errtrace
set -o nounset

export LC_ALL=C
unset CDPATH

: ${RELEASE_DEBUG:=false}

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

# Called when the script exit.
on_exit()
{
  cleanup
}

# Called when the script is interrupt with SIGINT.
on_interrupt()
{
  echo "Release script has been interrupted!!!"
  exit 2
}

# Check whether $1 is an absolute path name.
is_absolute()
{
  test -z "${1##/*}"
}

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
for version in 2.7.10 3.2.3 3.2.6 3.3.6 3.4.3
do
  PYENV_VERSION=$version python -m unittest test_pyloc
done

### Cleanup release/build directories
trap -- on_exit EXIT
trap -- on_interrupt INT
cleanup
rm -rf dist build pyloc.egg-info

### Generate and check version
VERSION=$(git describe --dirty --always --match 'v*' | sed -e 's/^v//')
echo "$VERSION" > VERSION.txt
grep -q -E '^[0-9]+\.[0-9]+\.[0-9]+$' VERSION.txt \
  || fatal "invalid version '$VERSION'"

### Build distribution
python setup.py sdist
python setup.py bdist_wheel --universal

### Test distribution
./distcheck.sh "$ME_DIR/dist/pyloc-$VERSION.tar.gz"

### Upload
twine upload dist/*

### Final cleanup
cleanup
