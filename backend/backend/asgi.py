"""ASGI entrypoint for the Foodgram backend."""

from __future__ import annotations

import os
from functools import lru_cache

from django.core.asgi import get_asgi_application
from django.core.handlers.asgi import ASGIHandler

SETTINGS_MODULE = "backend.settings"


def _configure_environment() -> None:
    """Ensure Django knows which settings module to use."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", SETTINGS_MODULE)


@lru_cache(maxsize=1)
def _build_application() -> ASGIHandler:
    """Return a cached ASGI application instance."""
    _configure_environment()
    return get_asgi_application()


application: ASGIHandler = _build_application()
