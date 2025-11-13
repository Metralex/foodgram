"""WSGI точка входа для бэкенда Foodgram."""

from __future__ import annotations

import os
from functools import lru_cache

from django.core.handlers.wsgi import WSGIHandler
from django.core.wsgi import get_wsgi_application

SETTINGS_MODULE = "backend.settings"


def _configure_environment() -> None:
    """Настроить Django для использования правильного модуля настроек."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", SETTINGS_MODULE)


@lru_cache(maxsize=1)
def _build_application() -> WSGIHandler:
    """Возвращает кэшированный экземпляр WSGI обработчика."""
    _configure_environment()
    return get_wsgi_application()


application: WSGIHandler = _build_application()
