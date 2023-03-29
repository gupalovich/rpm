# PRM4ALL

PRM4ALL description

## TODO
---

1. Core

2. Dashboard
    - Пагинация транзакций рефераллов
    - Объединить в PollToken, PollTokenRounds

3. Tokens
    - TokenTransaction
        - Убрать uuid / Добавить txhash

4. Users

5. Документация

6. Интернационализация
    - Английский
    - Испанский


## Начало работы
---
### Локально

1. Обновить example.env на .env
2. `set READ_DOT_ENV_FILE=TRUE`
3. В .env: <br>
    3.1. обновить DATABASE_URL и создать свою postgres бд <br>
    3.2. Добавить private key в `BSCSCAN_PRIVATE_KEY`. [Инструкция](https://support.metamask.io/hc/en-us/articles/360015289632-How-to-export-an-account-s-private-key) <br>
4. Закоментить hiredis в requirements/local.txt
5. `pip install -r requirements/local.txt`
6. `python manage.py migrate`
7. `python manage.py createsuperuser`
8. `python manage.py runserver`
9. Добавить переодическую таску `transactions_pooling` в админке

### Докер

- Локальная разработка
    - `docker-compose -f local.yml up --build`

- Продакшен
    - `docker-compose -f production.yml up --build`

- Создать суперюзера
    - `docker-compose -f local.yml run --rm django python manage.py createsuperuser`

## Фронтенд
---

    Стек gulp + sass. Только вне докера.
    Gulp минифицирует *.scss файлы, а BrowserSync проксирует порт 8000

    # Установка:
    npm install
    gulp


## Тестирование
---

### Mypy

    $ mypy prm

### Test coverage

    $ coverage run -m pytest
    $ coverage html
    $ open htmlcov/index.html

### Pytest

    $ pytest


## Celery
---
- Возможно тестирование вне докера / Проверка работы с докером


## Email Server
---

    Для локальной разработки в докер доступен mailhog, вне докера django-email-backend

    Mailhog работает на порту:
    http://localhost:8025/

## Докер:

### Полезные команды

    # containers status
    docker-compose -f production.yml ps

    # containers logs
    docker-compose -f production.yml logs

    # remove unused(dangling) images
    docker image prune

    # django shell run
    docker-compose -f production.yml run --rm django python manage.py shell

    # django dump db data
    docker-compose -f production.yml run --rm django bash
    python -Xutf8 manage.py dumpdata {app}.{Model -o data.json
      # Открыть вторую консоль, сохраняя сессию в старой
      docker cp 5f5cecd3798e:/app/data.json ./data.json

    # If you want to scale application
    # ❗ Don’t try to scale postgres, celerybeat, or traefik
    docker-compose -f production.yml up --scale django=4
    docker-compose -f production.yml up --scale celeryworker=2


## Документация
---

- Sphinx readthedocs

## Deployment
---

Инструкции по деплою.

### Sentry

Нужно задать переменные окружения SENTRY_DSN и опционально DJANGO_SENTRY_LOG_LEVEL
