Introduction
============

Detail basic command to know when hacking ``pyloc``.
All commands must be executed from the root of the repository.

Test suite
----------

Use this command to run the entire test suite::

    $ python -m unittest test_pyloc

or::

    $ nosetests

If you are using `pyenv <https://github.com/yyuu/pyenv>`_, you can run
the test suite against several version of python like this::

    for v in `pyenv versions --bare`; do
      echo ">>>>>>>>>>>>>> $v"
      PYENV_VERSION=$v python -m unittest test_pyloc
    done
