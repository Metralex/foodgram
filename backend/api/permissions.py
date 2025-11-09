from rest_framework.permissions import (
    SAFE_METHODS,
    IsAuthenticatedOrReadOnly,
)


class IsAuthorOrReadOnly(IsAuthenticatedOrReadOnly):
    """Модификация только автором, остальным - чтение."""

    message = "Изменять объект может только его автор."

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        if not hasattr(obj, 'author'):
            return False

        return obj.author == request.user
