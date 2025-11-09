import os
from functools import lru_cache

from django.core.asgi import get_asgi_application

DJANGO_SETTINGS_MODULE = "backend.settings"


@lru_cache
def create_asgi_app():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", DJANGO_SETTINGS_MODULE)
    return get_asgi_application()


application = create_asgi_app()
