"""
Конфигурация WSGI для проекта backend.

Предоставляет WSGI callable как переменную уровня модуля ``application``.

Дополнительная информация:
https://docs.djangoproject.com/en/3.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

application = get_wsgi_application()
