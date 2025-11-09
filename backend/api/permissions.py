from rest_framework.permissions import IsAuthenticatedOrReadOnly


class IsAuthorOrReadOnly(IsAuthenticatedOrReadOnly):
    """Allow unsafe operations only for the author of the object."""

    message = "Изменять объект может только его автор."

    def has_object_permission(self, request, view, obj):
        if super().has_object_permission(request, view, obj):
            return True
        author = getattr(obj, "author", None)
        return author is not None and author == request.user
