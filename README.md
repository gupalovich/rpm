# PRM4ALL

PRM4ALL description

## TODO
---

1. User
    - User admin inlines - разобраться в инлайн настройках пользователя

2. Core
    - Таски
        - Обновление total_amount_sold раунда
        - Переход с одного раунда на другой
        - Задача на обновление token_balance пользователя

3. Tokens
    - Перегон из BNB в $ на фронте
    - Автоматизация создания Token и TokenRound

4. Dashboard
    - Обработка формы "buy tokens"
        - ~~Обработка post запроса для формы и сохранение транзакции~~
        - Перевод формы в ajax
        - В беке добавить статус транзакции. Создавать её, как только пользователь нажал кнопку "Купить", со статусом "PENDING". Как только транзакция на стороне метамаска прошла, отправлять xhr со статусом ответа и обновлять статус транзакции
    - HTMX
    - Ссылка для приглашения
    - Маленький аватар некоректный размер
    - ProfileUserUpdateForm добавить больше валидации + тестирование
        - Проверка полей имя/фамилия/город на плохие слова

5. Документация

6. Интернационализация
    - Английский
    - Испанский

7. Misc
    - Sitemap


## Начало работы
---
### Локально

1. Обновить example.env на .env
2. `set READ_DOT_ENV_FILE=TRUE`
3. В .env обновить DATABASE_URL и создать свою postgres бд
4. Закоментить hiredis в requirements/local.txt
5. `pip install -r requirements/local.txt`
6. `python manage.py migrate`
7. `python manage.py createsuperuser`
8. `python manage.py runserver`

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

## Документация
---

- Sphinx readthedocs

## Deployment
---

Инструкции по деплою.

### Sentry

Нужно задать переменные окружения SENTRY_DSN и опционально DJANGO_SENTRY_LOG_LEVEL
