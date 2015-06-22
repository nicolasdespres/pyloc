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
