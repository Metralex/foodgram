from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ApiConfig(AppConfig):
    """Application configuration for the public API."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "api"
    verbose_name = _("Foodgram API")

    def ready(self):
        # Import modules that register signals or other application hooks.
        from . import utils  # noqa: WPS433, F401
