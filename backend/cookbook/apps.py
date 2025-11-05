"""Configuration for the cookbook application."""
from django.apps import AppConfig


class CookbookConfig(AppConfig):
    """Application configuration for culinary content management."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cookbook'
    verbose_name = 'Culinary Content'
