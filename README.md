# PRM4ALL

PRM4ALL description

## TODO
---

1. User
    - ~~Добавить parent, token_balance, metamask_wallet, metamask_confirmed~~
        - Тестирование новых полей
    - Добавление реферальной системы
        - Формирование реферальной ссылки и соответствующего view редиректа
        - Тестирование реферальной системы
    - Добавление таблицы Settings
        - Обновление форм
        - Тестирование
    - Добавление app tokens
        - Token, TokenRound, TokenTransaction
        - Тестирование моделей

2. Dashboard
    - ProfileUserUpdateForm добавить больше валидации + тестирование
    - Найти место для блока messages
    - Profile адаптив формы
    - Profile неверное отображение ошибок в grid
    - Custom checkbox
    - Team проверить элементы блоков myteam и начисления
    - Запрет на повторное изменение кошелька метамаск

2. Документация

3. Интернационализация
    - Английский, испанский

3. Перегон из BNB в $ на фронте


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
