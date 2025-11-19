"""Конфигурация приложения API."""

from django.apps import AppConfig


class ApiConfig(AppConfig):

    """Настройка приложения API для работы с рецептами."""

    name = 'api'
    default_auto_field = 'django.db.models.BigAutoField'
