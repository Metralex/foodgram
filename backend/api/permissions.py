"""
API permissions for foodgram application.

This module contains permission classes for controlling access
to API endpoints based on user roles and object ownership.
"""
from typing import TYPE_CHECKING

from rest_framework.permissions import SAFE_METHODS, IsAuthenticatedOrReadOnly

if TYPE_CHECKING:
    from rest_framework.request import Request
    from rest_framework.views import APIView
    from recipes.models import Recipe


class IsAuthorOrReadOnly(IsAuthenticatedOrReadOnly):
    """
    Permission class for recipe operations.

    Allows read access to all users, but write access only to recipe authors.
    """

    def has_object_permission(
        self, request: 'Request', view: 'APIView', obj: 'Recipe'
    ) -> bool:
        """
        Check if user has permission to perform action on recipe.

        Args:
            request: HTTP request object.
            view: View instance.
            obj: Recipe instance.

        Returns:
            True if user has permission, False otherwise.
        """
        # Read permissions are allowed for any request
        if request.method in SAFE_METHODS:
            return True

        # Write permissions are only allowed to the author
        return obj.author == request.user
