# Introduction

Detail basic command to know when hacking `pyloc`.
All commands must be executed from the root of the repository.

## Test suite

```sh
python -m unittest test_pyloc
```

or

```sh
nosetests
```

If you are using [pyenv](https://github.com/yyuu/pyenv), you can run
the test suite against several version of python like this:

```sh
for v in 2.7.9 3.2.3 3.4.2 3.4.3; do
  echo ">>>>>>>>>>>>>> $v"
  PYENV_VERSION=$v python -m unittest test_pyloc
done
```
