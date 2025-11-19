"""Конфигурация приложения рецептов."""

from django.apps import AppConfig


class RecipesConfig(AppConfig):

    """Настройка приложения для работы с рецептами."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'recipes'
