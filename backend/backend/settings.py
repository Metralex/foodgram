"""
Настройки Django для проекта backend.

Сгенерировано с помощью 'django-admin startproject' используя Django 4.2.16.

Дополнительная информация:
https://docs.djangoproject.com/en/4.2/topics/settings/
https://docs.djangoproject.com/en/4.2/ref/settings/
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Базовый путь проекта
BASE_DIR = Path(__file__).resolve().parent.parent

# Загрузка переменных окружения из файла .env
load_dotenv(BASE_DIR / '.env')

# ============================================================================
# БЕЗОПАСНОСТЬ
# ============================================================================

# Секретный ключ для подписи данных сессий и токенов
# ВНИМАНИЕ: храните секретный ключ в безопасности в продакшене!
SECRET_KEY = os.getenv('SECRET_KEY', '')

# Режим отладки
# ВНИМАНИЕ: не включайте DEBUG=True в продакшене!
DEBUG = os.getenv('DEBUG', 'True') == 'True'

# Разрешенные хосты для обработки запросов
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '127.0.0.1,').split(',')

# ============================================================================
# КОНФИГУРАЦИЯ ПРИЛОЖЕНИЙ
# ============================================================================

INSTALLED_APPS = [
    # Стандартные приложения Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Сторонние приложения
    'django_extensions',
    'rest_framework.authtoken',
    'rest_framework',
    'django_filters',
    'djoser',
    # Локальные приложения
    'accounts',      # Управление пользователями и социальными связями
    'cookbook',      # Кулинарный контент (рецепты, ингредиенты, категории)
    'gateway',       # API слой (эндпоинты, сериализаторы, фильтры)
]

# ============================================================================
# MIDDLEWARE
# ============================================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Корневой модуль URL конфигурации
ROOT_URLCONF = 'backend.urls'

# ============================================================================
# ШАБЛОНЫ
# ============================================================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# WSGI приложение для развертывания
WSGI_APPLICATION = 'backend.wsgi.application'

# ============================================================================
# БАЗА ДАННЫХ
# ============================================================================

# Поддержка SQLite (по умолчанию) и PostgreSQL (для продакшена)
if os.getenv('USE_SQLITE', 'True') == 'True':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db/db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('POSTGRES_DB', ''),
            'USER': os.getenv('POSTGRES_USER', ''),
            'PASSWORD': os.getenv('POSTGRES_PASSWORD', ''),
            'HOST': os.getenv('POSTGRES_DB_HOST', 'db'),
            'PORT': os.getenv('POSTGRES_DB_PORT', 5432),
        }
    }

# ============================================================================
# ВАЛИДАЦИЯ ПАРОЛЕЙ
# ============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ============================================================================
# ИНТЕРНАЦИОНАЛИЗАЦИЯ
# ============================================================================

LANGUAGE_CODE = os.getenv('LANGUAGE_CODE', 'ru-RU')
TIME_ZONE = os.getenv('TIME_ZONE', 'UTC')

USE_I18N = True  # Включить интернационализацию
USE_L10N = True  # Включить локализацию
USE_TZ = True    # Использовать часовые пояса

# ============================================================================
# СТАТИЧЕСКИЕ ФАЙЛЫ И МЕДИА
# ============================================================================

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'collected_static'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ============================================================================
# ПОЛЬЗОВАТЕЛЬСКАЯ МОДЕЛЬ
# ============================================================================

AUTH_USER_MODEL = 'accounts.Account'

# ============================================================================
# REST FRAMEWORK
# ============================================================================

REST_FRAMEWORK = {
    # Классы разрешений по умолчанию
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    # Классы аутентификации по умолчанию
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    # Класс пагинации по умолчанию
    'DEFAULT_PAGINATION_CLASS': 'gateway.pagination.ConfigurablePagePagination',
    'PAGE_SIZE': 6,
}

# ============================================================================
# DJOSER (Аутентификация и управление пользователями)
# ============================================================================

DJOSER = {
    'HIDE_USERS': False,
    'SERIALIZERS': {
        'user': 'gateway.serializers.AccountSerializer',
        'current_user': 'gateway.serializers.AccountSerializer',
    },
    'PERMISSIONS': {
        'user': ('djoser.permissions.CurrentUserOrAdminOrReadOnly',),
        'user_list': ('rest_framework.permissions.AllowAny',),
    },
}

# ============================================================================
# CORS (Cross-Origin Resource Sharing)
# ============================================================================

# Регулярное выражение для URL, к которым применяется CORS
CORS_URLS_REGEX = r'^/api/.*$'

# Разрешенные источники для CORS запросов
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
]

# ============================================================================
# EMAIL
# ============================================================================

# Бэкенд для отправки email (в разработке - файловый)
EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = './email'

# ============================================================================
# ВАЛИДАЦИЯ ИМЕН ПОЛЬЗОВАТЕЛЕЙ
# ============================================================================

# Паттерн для валидации имен пользователей
USERNAME_PATTERN = r'[\w.@+-]'

# Запрещенные имена пользователей
FORBIDDEN_USERNAMES = ('me',)

# ============================================================================
# ПУТИ ДЛЯ ЗАГРУЗКИ ФАЙЛОВ
# ============================================================================

AVATARS_PATH = 'users/avatars'
RECIPES_IMAGES_PATH = 'recipes/images/'

# ============================================================================
# ПРОКСИ И SSL
# ============================================================================

# Использовать заголовок X-Forwarded-Host
USE_X_FORWARDED_HOST = True

# Заголовок для определения протокола через прокси
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# ============================================================================
# CSRF
# ============================================================================

# Доверенные источники для CSRF защиты
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
]
