"""
Конфигурация ASGI для проекта backend.

Предоставляет ASGI callable как переменную уровня модуля ``application``.

Дополнительная информация:
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

application = get_asgi_application()
