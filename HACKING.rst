Introduction
============

Detail basic command to know when hacking ``pyloc``.
All commands must be executed from the root of the repository.

Test suite
----------

Use this command to run the entire test suite:

.. code:: bash

    $ python -m unittest test_pyloc

or:

.. code:: bash

    $ nosetests

If you are using `pyenv <https://github.com/yyuu/pyenv>`_, you can run
the test suite against several version of python like this:

.. code:: bash

    for v in `pyenv versions --bare`; do
      echo ">>>>>>>>>>>>>> $v"
      PYENV_VERSION=$v python -m unittest test_pyloc
    done

How to make a release
---------------------

1. Update python version in runtests.sh. We use the last micro release
   for each pair of major.minor version supported.

2. Write a tag message containing the release notes. You can get the
   list of new commits since the last release using this command:

   .. code:: bash

       $ git log $(git describe --always --match 'v*' --abbrev=0)..master

   Store you tag message in a file called '/tmp/pyloc.tagmsg' for
   instance.

3. Make sure local commits are pushed.

4. Check that Travis.CI has successfully checked the last commit.

5. Make a test release on testpypi.python.org server and check that it
   is ok (mainly the information text should be well formatted).

   .. code:: bash

       $ ./release.sh --tag-msg=/tmp/pyloc.tagmsg --repo=pypitest --no-push $VERSION

6. Make the release:

   .. code:: bash

       $ ./release.sh --tag-msg=/tmp/pyloc.tagmsg --repo=pypi $VERSION
