================
Welcome to pyloc
================

*pyloc* prints the location of the definition of any python object in
your file-system.

Introduction
============

*pyloc* is very similar to what ``python3 -m inspect -d <object>``
offers. However, it is only focused to retrieve the file name (and
eventually the line number) defining a given Python object. The object
can be a package, module, class, method or function.

*pyloc* makes some further effort to figure out the line and column number and
its outputs is formatted so that it can easily be passed to ``emacsclient``
or ``vi``.

*pyloc* works with Python 2.7, 3.2, 3.3 and 3.4.

Examples
========

You can see the location of ``Popen.wait`` method in the sub-process package::

    $ python -m pyloc -f human subprocess:Popen.wait
    Filename: /Users/polrop/.pyenv/versions/2.7.9/lib/python2.7/subprocess.py
    Line: 1379

    $ python -m pyloc -f human email.utils:formataddr
    Filename: /Users/polrop/.pyenv/versions/2.7.9/lib/python2.7/email/utils.py
    Line: 85

(Output may be different on your system since you have different
installation path and version)

Note that the object naming syntax is as follow: ``module[:qualname]``

To open it in Emacs you can do::

    $ emacsclient `python -m pyloc -f emacs subprocess:Popen.wait`

or in vim::

    $ vim `python -m pyloc -f vi subprocess:Popen.wait`

If you are lazy typing ``-f <format>`` all the time and you often use
the same format, you can set the default output format this way (you
can add this line in your ``.zshenv`` or ``.bashrc``)::

    $ export PYLOC_DEFAULT_FORMAT=emacs

*pyloc* will always locate object based on the ``python`` interpreter
your are using::

    $ python3 -m pyloc -f human subprocess:Popen.wait
    Filename: /Users/polrop/.pyenv/versions/3.4.3/lib/python3.4/subprocess.py
    Line: 1526

    $ /usr/local/bin/python -m pyloc -f human email.utils:formataddr
    Filename: /usr/local/Cellar/python/2.7.9/Frameworks/Python.framework/Versions/2.7/lib/python2.7/email/utils.py
    Line: 85

    $ /usr/bin/python -m pyloc -f human email.utils:formataddr
    Filename: /System/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/email/utils.py
    Line: 85

Installation
============

pip
---

You can install _pyloc_ using ``pip`` like this::

    $ pip install pyloc

or::

    $ pip3 install pyloc

From source
-----------

Clone this repository and run::

    $ python setup.py develop

Known bugs
==========

* Class or built-in types like int or str do not contain location
  information. In this case *pyloc* tries to look for the name in the
  AST. Since procedure may not be accurate since Python is a dynamic
  language.

Hacking
=======

See `HACKING <HACKING.rst>`_ for details.

License
=======

*pyloc* is released under the term of the
`Simplified BSD License <http://choosealicense.com/licenses/bsd-2-clause>`_.
Copyright (c) 2015, Nicolas Desprès
All rights reserved.

As noted in the source code, some part has been inspired by code from
the ``inspect`` module written by Ka-Ping Yee <ping@lfw.org> and
Yury Selivanov <yselivanov@sprymix.com> form the Python 3.4.3
distribution (see the LICENSE file in the python distribution)
