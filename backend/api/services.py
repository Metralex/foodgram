"""
Business logic services for API operations.

This module contains service classes that handle business logic
separated from views for better maintainability and testability.
"""
from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from rest_framework.exceptions import ValidationError

from recipes.constants import Error
from recipes.models import Favorite, Recipe, ShoppingCart, Subscription

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser

User = get_user_model()


class SubscriptionService:
    """Service for managing user subscriptions."""

    @staticmethod
    def subscribe(
        subscriber: 'AbstractUser', author: 'AbstractUser'
    ) -> Subscription:
        """
        Create a subscription from subscriber to author.

        Args:
            subscriber: User who wants to subscribe.
            author: User to subscribe to.

        Returns:
            Subscription: Created subscription instance.

        Raises:
            ValidationError: If subscription already exists or
                            user tries to subscribe to themselves.
        """
        if subscriber == author:
            raise ValidationError(
                dict(error=Error.CANNOT_SUBSCRIBE_TO_YOURSELF)
            )

        subscription, created = Subscription.objects.get_or_create(
            author=author, subscriber=subscriber
        )
        if not created:
            raise ValidationError(dict(error=Error.ALREADY_SUBSCRIBED))

        return subscription

    @staticmethod
    def unsubscribe(
        subscriber: 'AbstractUser', author: 'AbstractUser'
    ) -> None:
        """
        Remove subscription from subscriber to author.

        Args:
            subscriber: User who wants to unsubscribe.
            author: User to unsubscribe from.

        Raises:
            Http404: If subscription does not exist.
        """
        from django.shortcuts import get_object_or_404
        get_object_or_404(
            Subscription, author=author, subscriber=subscriber
        ).delete()

    @staticmethod
    def get_subscriptions_queryset(user: 'AbstractUser') -> QuerySet:
        """
        Get queryset of users that the given user is subscribed to.

        Args:
            user: User to get subscriptions for.

        Returns:
            QuerySet of User instances.
        """
        return User.objects.filter(authors__subscriber=user)


class RecipeInteractionService:
    """Service for managing recipe interactions (favorites, shopping cart)."""

    @staticmethod
    def add_to_favorites(user: 'AbstractUser', recipe: Recipe) -> Favorite:
        """
        Add recipe to user's favorites.

        Args:
            user: User who wants to favorite the recipe.
            recipe: Recipe to add to favorites.

        Returns:
            Favorite: Created favorite instance.

        Raises:
            ValidationError: If recipe is already in favorites.
        """
        favorite, created = Favorite.objects.get_or_create(
            user=user, recipe=recipe
        )
        if not created:
            raise ValidationError(dict(error=Error.ALREADY_FAVORITED))
        return favorite

    @staticmethod
    def remove_from_favorites(user: 'AbstractUser', recipe: Recipe) -> None:
        """
        Remove recipe from user's favorites.

        Args:
            user: User who wants to remove the recipe.
            recipe: Recipe to remove from favorites.

        Raises:
            Http404: If favorite does not exist.
        """
        from django.shortcuts import get_object_or_404
        get_object_or_404(Favorite, user=user, recipe=recipe).delete()

    @staticmethod
    def add_to_shopping_cart(
        user: 'AbstractUser', recipe: Recipe
    ) -> ShoppingCart:
        """
        Add recipe to user's shopping cart.

        Args:
            user: User who wants to add the recipe.
            recipe: Recipe to add to shopping cart.

        Returns:
            ShoppingCart: Created shopping cart instance.

        Raises:
            ValidationError: If recipe is already in shopping cart.
        """
        cart_item, created = ShoppingCart.objects.get_or_create(
            user=user, recipe=recipe
        )
        if not created:
            raise ValidationError(
                dict(error=Error.ALREADY_IN_SHOPPING_CART)
            )
        return cart_item

    @staticmethod
    def remove_from_shopping_cart(
        user: 'AbstractUser', recipe: Recipe
    ) -> None:
        """
        Remove recipe from user's shopping cart.

        Args:
            user: User who wants to remove the recipe.
            recipe: Recipe to remove from shopping cart.

        Raises:
            Http404: If shopping cart item does not exist.
        """
        from django.shortcuts import get_object_or_404
        get_object_or_404(
            ShoppingCart, user=user, recipe=recipe
        ).delete()
