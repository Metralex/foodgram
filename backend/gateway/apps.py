"""Configuration for the gateway application."""
from django.apps import AppConfig


class GatewayConfig(AppConfig):
    """Application configuration for API gateway layer."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gateway'
    verbose_name = 'API Gateway'
