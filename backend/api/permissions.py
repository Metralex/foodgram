"""
Разрешения для API приложения Foodgram.

Модуль содержит классы разрешений для контроля доступа
к API endpoints на основе ролей пользователей и владения объектом.
"""
from typing import TYPE_CHECKING

from rest_framework.permissions import SAFE_METHODS, IsAuthenticatedOrReadOnly

if TYPE_CHECKING:
    from rest_framework.request import Request
    from rest_framework.views import APIView
    from recipes.models import Recipe


class IsAuthorOrReadOnly(IsAuthenticatedOrReadOnly):
    """
    Класс разрешения для операций с блюдами.

    Позволяет доступ на чтение всем пользователям, но доступ на запись
    только авторам блюда.
    """

    def has_object_permission(
        self, request: 'Request', view: 'APIView', obj: 'Recipe'
    ) -> bool:
        """
        Проверить, имеет ли пользователь разрешение выполнять
        действие с блюдом.

        Аргументы:
            request: Объект HTTP запроса.
            view: Экземпляр представления.
            obj: Экземпляр блюда.

        Возвращает:
            True если пользователь имеет разрешение, False в противном
            случае.
        """
        # Разрешения на чтение доступны для любого запроса
        if request.method in SAFE_METHODS:
            return True

        # Разрешения на запись только для автора
        return obj.author == request.user
