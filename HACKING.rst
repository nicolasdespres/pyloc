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

or using ``tox`` (make sure all python environment set in ``tox.ini``
are installed in ``pyenv`` and that they are made globally available using for
instance: ``pyenv global 2.7.11 3.5.1 3.4.3 3.3.6 3.2.6``)

.. code:: bash

    tox

How to make a release
---------------------

#. Write a tag message containing the release notes. You can get the
   list of new commits since the last release using this command:

   .. code:: bash

       $ git log $(git describe --always --match 'v*' --abbrev=0)..master

   Store you tag message in a file called '/tmp/pyloc.tagmsg' for
   instance.

#. Make sure local commits are pushed.

#. Check that Travis.CI has successfully checked the last commit.

#. Choose a release version and store it in a ``VERSION`` shell variable:

   * Release number are of the form X.Y.Z.
   * Pre-release number are of the form X.Y.ZrcN
   * Post-release number are of the form X.Y.Z-N. This kind of release
     is supported only for continuous integration system and are *not
     tagged*. Do not pass any version number or tag message as
     argument to the release script to make such a release.
     If you want to make a bug fix release just increment the
     Z number.

#. Make a test release on testpypi.python.org server and check that it
   is ok (mainly the information text should be well formatted).

   **Make sure the ``--push`` flag is not set and the repo is ``pypitest``**

   .. code:: bash

       $ ./release.sh --tag-msg=/tmp/pyloc.tagmsg --upload=pypitest --clean $VERSION

#. Visit ``https://testpypi.python.org/pypi/pyloc/$VERSION`` and check
   that all looks good.

#. Test that installation is ok form ``pypitest``:

   .. code:: bash

       $ PYENV_VERSION=2.7.11 virtualenv testinstall2
       $ cd testinstall2
       $ source bin/activate
       $ pip install --index-url https://testpypi.python.org/pypi --ignore-installed 'pyloc==$VERSION'
       $ rehash
       $ pyloc --version  # check version and revision is correct
       $ pyloc2 --version # check version and revision is correct
       $ deactivate
       $ cd ..
       $ rm -rf testinstall2

       $ PYENV_VERSION=3.5.1 virtualenv testinstall3
       $ cd testinstall3
       $ source bin/activate
       $ pip install --index-url https://testpypi.python.org/pypi --ignore-installed 'pyloc==$VERSION'
       $ rehash
       $ pyloc --version  # check version and revision is correct
       $ pyloc3 --version # check version and revision is correct
       $ deactivate
       $ cd ..
       $ rm -rf testinstall2

#. Make the release:

   .. code:: bash

       $ ./release.sh --tag-msg=/tmp/pyloc.tagmsg --upload=pypi --push $VERSION

#. Unset the ``VERSION`` shell variable.
