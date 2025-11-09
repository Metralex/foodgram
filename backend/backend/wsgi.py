"""WSGI entrypoint used by the Foodgram project."""

from __future__ import annotations

import os
from functools import lru_cache

from django.core.wsgi import get_wsgi_application

DJANGO_SETTINGS_MODULE = "backend.settings"


@lru_cache
def create_wsgi_app():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", DJANGO_SETTINGS_MODULE)
    return get_wsgi_application()


application = create_wsgi_app()
