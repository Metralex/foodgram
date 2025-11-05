"""Конфигурация для приложения accounts."""
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Конфигурация приложения для управления аккаунтами."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    verbose_name = 'User Accounts'
