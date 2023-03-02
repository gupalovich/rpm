# PRM4ALL

    Что из себя представляет, в кратце:
    - Регистрация/вход/подтверждение из коробки
    - поддержка докера
    - поддержка редиса
    - поддержка celery


## Settings

Moved to [settings](http://cookiecutter-django.readthedocs.io/en/latest/settings.html).

## Basic Commands

### Type checks

Running type checks with mypy:

    $ mypy prm

### Test coverage

To run the tests, check your test coverage, and generate an HTML coverage report:

    $ coverage run -m pytest
    $ coverage html
    $ open htmlcov/index.html

#### Running tests with pytest

    $ pytest

## Deployment

The following details how to deploy this application.

### Docker

See detailed [cookiecutter-django Docker documentation](http://cookiecutter-django.readthedocs.io/en/latest/deployment-with-docker.html).
