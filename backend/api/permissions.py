"""Классы прав доступа для API Foodgram."""

from rest_framework.permissions import SAFE_METHODS, IsAuthenticatedOrReadOnly


class IsAuthorOrReadOnly(IsAuthenticatedOrReadOnly):
    """Разрешение на изменение только автором объекта."""

    message = "Изменять объект может только его автор."

    def has_object_permission(self, request, view, obj):
        """Проверяет права доступа пользователя к объекту."""
        if request.method in SAFE_METHODS:
            return True

        if not hasattr(obj, "author"):
            return False

        return obj.author == request.user
