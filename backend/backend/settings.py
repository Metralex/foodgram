from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, List

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _env_bool(name: str, default: bool = False) -> bool:
    """Return a boolean interpreted from an environment variable."""
    truthy = {"1", "true", "t", "yes", "y", "on"}
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in truthy


def _env_list(name: str, default: Iterable[str] | None = None) -> List[str]:
    """Parse a comma-separated environment variable into a list."""
    raw_value = os.getenv(name)
    if raw_value is None:
        if default is None:
            return []
        return [item.strip() for item in default if item.strip()]
    return [item.strip() for item in raw_value.split(",") if item.strip()]


SECRET_KEY = os.getenv("SECRET_KEY", "")
DEBUG = _env_bool("DEBUG", default=True)
ALLOWED_HOSTS = _env_list("ALLOWED_HOSTS", default=("127.0.0.1",))


INSTALLED_APPS = [
    # Django apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party apps
    "django_extensions",
    "rest_framework.authtoken",
    "rest_framework",
    "django_filters",
    "djoser",
    # Local apps
    "api",
]


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "backend.urls"


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "backend.wsgi.application"

if _env_bool("USE_SQLITE", default=True):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db/db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("POSTGRES_DB", ""),
            "USER": os.getenv("POSTGRES_USER", ""),
            "PASSWORD": os.getenv("POSTGRES_PASSWORD", ""),
            "HOST": os.getenv("POSTGRES_DB_HOST", "db"),
            "PORT": os.getenv("POSTGRES_DB_PORT", 5432),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = os.getenv("LANGUAGE_CODE", "ru-RU")
TIME_ZONE = os.getenv("TIME_ZONE", "UTC")

USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "collected_static"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

AUTH_USER_MODEL = "api.User"

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PAGINATION_CLASS": "api.pagination.LimitPageNumberPagination",
    "PAGE_SIZE": 6,
}

DJOSER = {
    "HIDE_USERS": False,
    "SERIALIZERS": {
        "user": "api.serializers.UserSerializer",
        "current_user": "api.serializers.UserSerializer",
    },
    "PERMISSIONS": {
        "user": ("djoser.permissions.CurrentUserOrAdminOrReadOnly",),
        "user_list": ("rest_framework.permissions.AllowAny",),
    },
}

CORS_URLS_REGEX = r"^/api/.*$"
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
]

EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
EMAIL_FILE_PATH = "./email"

USERNAME_PATTERN = r"[\w.@+-]"
FORBIDDEN_USERNAMES = ("me",)

AVATARS_PATH = "users/avatars"
RECIPES_IMAGES_PATH = "recipes/images/"

USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")


def _parse_csrf_origins() -> List[str]:
    """Return trusted origins defined via environment variables."""
    return _env_list("CSRF_TRUSTED_ORIGINS")


CSRF_TRUSTED_ORIGINS = _parse_csrf_origins()
