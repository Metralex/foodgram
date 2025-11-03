<div align="center">

# Foodgram – социальная сеть для обмена рецептами

[![CI/CD](https://github.com/Metralex/foodgram/actions/workflows/main.yml/badge.svg)](https://github.com/Metralex/foodgram/actions/workflows/main.yml)

</div>

## О проекте

Foodgram — это сервис для публикации и обмена кулинарными рецептами. Пользователи могут
создавать собственные блюда, просматривать ленту, фильтровать рецепты по тегам,
подписываться на авторов, сохранять понравившиеся блюда в избранное и формировать список
покупок с автоматическим подсчётом ингредиентов. Платформа состоит из адаптированного
backend на Django/DRF (поддерживает исторический API Postman коллекции) и SPA-интерфейса на React, который
отдаётся через Nginx.

Ключевые возможности:

- регистрация, авторизация и управление профилем (аватар, смена пароля);
- публикация рецептов с тегами, ингредиентами, фото и временем приготовления;
- короткие ссылки на рецепты (`/s/<код>/`), которые можно делиться во внешних ресурсах;
- подписки на авторов и отдельная страница с их последними публикациями;
- избранные рецепты и корзина покупок с выгрузкой агрегированного списка ингредиентов (`.txt`);
- поиск ингредиентов по префиксу и фильтрация рецептов на главной, в избранном и на странице автора;
- Postman-коллекция и redoc-документация для тестирования API;
- CI/CD: линтеры и тесты, сборка Docker-образов, деплой на сервер и уведомления в Telegram.

## Стек технологий

| Слой          | Технологии                                                                 |
|---------------|-----------------------------------------------------------------------------|
| Backend       | Python 3.9, Django 4.2, Django REST Framework, Djoser, django-filter, Gunicorn |
| Frontend      | React, Node.js 21, SPA со статической сборкой                             |
| База данных   | PostgreSQL 13 (по умолчанию), SQLite (для локальной разработки)           |
| Инфраструктура| Docker & Docker Compose, Nginx, GitHub Actions, Docker Hub, bash/ssh       |
| Утилиты       | python-dotenv, flake8, management-команды для импорта CSV, Postman         |

## Содержание

1. [Быстрый старт (Docker)](#быстрый-старт-docker)
2. [Локальная разработка без Docker](#локальная-разработка-без-docker)
3. [Переменные окружения](#переменные-окружения)
4. [Полезные команды](#полезные-команды)
5. [CI/CD](#cicd)
6. [Полезные ссылки](#полезные-ссылки)
7. [Автор](#автор)

## Быстрый старт (Docker)

### 1. Клонирование репозитория

```bash
git clone https://github.com/Metralex/foodgram.git
cd foodgram
```

### 2. Настройка переменных окружения

Создайте файл `backend/.env` (этот путь читает Django) со значениями:

```env
SECRET_KEY=укажите-случайную-строку
DEBUG=False
ALLOWED_HOSTS=127.0.0.1,localhost
CSRF_TRUSTED_ORIGINS=http://127.0.0.1,http://localhost

# Используйте SQLite=True для локального запуска без PostgreSQL
USE_SQLITE=True

# Настройки PostgreSQL (используются, если USE_SQLITE=False)
POSTGRES_DB=foodgram
POSTGRES_USER=foodgram
POSTGRES_PASSWORD=foodgram_password
POSTGRES_DB_HOST=db
POSTGRES_DB_PORT=5432
```

> ⚠️ В production установите `DEBUG=False`, пропишите реальные домены в `ALLOWED_HOSTS` и
> `CSRF_TRUSTED_ORIGINS`, используйте надёжные пароли и `USE_SQLITE=False`.

Docker Compose ожидает .env рядом с файлом `docker-compose.production.yml`, поэтому скопируйте созданный файл:

```bash
cp backend/.env .env
```

### 3. Сборка и запуск контейнеров

```bash
docker compose -f infra/docker-compose.production.yml up -d --build
```

### 4. Миграции, статика, суперпользователь

```bash
docker compose -f infra/docker-compose.production.yml exec backend python manage.py migrate
docker compose -f infra/docker-compose.production.yml exec backend python manage.py collectstatic --no-input
docker compose -f infra/docker-compose.production.yml exec backend python manage.py createsuperuser
```

### 5. Импорт справочников

```bash
docker compose -f infra/docker-compose.production.yml exec backend python manage.py import_ingredients
docker compose -f infra/docker-compose.production.yml exec backend python manage.py import_tags
```

### 6. Проверка

- Web-интерфейс: http://localhost:10000/
- Админка: http://localhost:10000/admin/
- Документация (Redoc): http://localhost:10000/api/docs/
- Скачивание списка покупок: http://localhost:10000/api/recipes/download_shopping_cart/

## Локальная разработка без Docker

```bash
python -m venv venv
source venv/Scripts/activate    # Windows: venv\Scripts\activate
pip install -r backend/requirements.txt
cd backend
python manage.py migrate
python manage.py runserver
```

После запуска локально также доступны команды `import_ingredients` и `import_tags` для наполнения справочников.

## Переменные окружения

| Переменная               | Назначение                                         | Значение по умолчанию |
|--------------------------|----------------------------------------------------|-----------------------|
| `SECRET_KEY`             | Секретный ключ Django                              | пусто                 |
| `DEBUG`                  | Режим отладки (`True/False`)                       | `True`                |
| `ALLOWED_HOSTS`          | Список доменов через запятую                       | `127.0.0.1,`          |
| `CSRF_TRUSTED_ORIGINS`   | Доверенные источники для CSRF                      | пусто                 |
| `USE_SQLITE`             | Использовать SQLite вместо PostgreSQL              | `True`                |
| `POSTGRES_DB`            | Имя БД PostgreSQL                                  | пусто                 |
| `POSTGRES_USER`          | Пользователь БД                                    | пусто                 |
| `POSTGRES_PASSWORD`      | Пароль пользователя БД                             | пусто                 |
| `POSTGRES_DB_HOST`       | Хост сервиса БД (в Docker — `db`)                  | `db`                  |
| `POSTGRES_DB_PORT`       | Порт сервиса БД                                    | `5432`                |

## Полезные команды

```bash
# Внутри контейнера backend или локального venv
python manage.py import_ingredients
python manage.py import_tags
python manage.py createsuperuser

# Линтинг и тесты
python -m flake8 backend/
cd backend && python manage.py test

# Выгрузка списка покупок через API
GET /api/recipes/download_shopping_cart/
```

## CI/CD

Workflow `.github/workflows/main.yml` выполняет:

1. Развёртывание матрицы Python 3.8–3.12, запуск flake8 и unit-тестов.
2. Сборку и публикацию Docker-образов backend и frontend в Docker Hub (только ветки `main`/`master`).
3. Деплой на удалённый сервер через SSH (`docker compose`), обновление миграций и статики.
4. Уведомления в Telegram о результатах (успех/ошибка).

## Полезные ссылки

- [Postman-коллекция](postman_collection/foodgram.postman_collection.json)
- [OpenAPI (schema)](docs/openapi-schema.yml)
- [Redoc (HTML)](docs/redoc.html)

## Автор

Проект разработан **Metralex** — <https://github.com/Metralex>

Связь, предложения и багрепорты — через Issues или Pull Requests в репозитории.

