"""Классы прав доступа для API Foodgram."""

from __future__ import annotations

from typing import Any

from django.http import HttpRequest
from rest_framework.permissions import (
    SAFE_METHODS,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.views import APIView


class IsAuthorOrReadOnly(IsAuthenticatedOrReadOnly):
    """Разрешение на изменение только автором объекта."""

    message = "Изменять объект может только его автор."

    def has_object_permission(
        self, request: HttpRequest, view: APIView, obj: Any
    ) -> bool:
        """Проверяет права доступа пользователя к объекту."""
        # Allow read-only requests for everyone
        if request.method in SAFE_METHODS:
            return True

        # Ensure the object has an author attribute
        if not hasattr(obj, "author"):
            return False

        # Only the author can modify the object
        return obj.author == request.user
