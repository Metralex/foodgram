"""Permission classes for API endpoint access control."""
from typing import TYPE_CHECKING

from rest_framework.permissions import (
    SAFE_METHODS,
    IsAuthenticatedOrReadOnly,
)

if TYPE_CHECKING:
    from rest_framework.request import Request
    from rest_framework.views import APIView
    from cookbook.models import CulinaryItem


class OwnerOrReadOnly(IsAuthenticatedOrReadOnly):
    """
    Permission class enforcing ownership-based write access.

    Allows read access to all users, but restricts write operations
    (create, update, delete) to the owner of the resource.
    """

    def has_object_permission(
        self, request: 'Request', view: 'APIView', obj: 'CulinaryItem'
    ) -> bool:
        """
        Check if the request has permission for the object.

        Args:
            request: The HTTP request object.
            view: The view instance handling the request.
            obj: The object being accessed.

        Returns:
            True if permission is granted, False otherwise.
        """
        if request.method in SAFE_METHODS:
            return True

        return obj.author == request.user
