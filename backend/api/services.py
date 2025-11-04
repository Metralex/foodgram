"""
Бизнес-логика для операций API.

Модуль содержит классы-сервисы, которые обрабатывают бизнес-логику,
отделённую от обработчиков для лучшей поддерживаемости и тестируемости.
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


class FollowingProvider:
    """Сервис для управления подписками между пользователями."""

    @staticmethod
    def subscribe(
        subscriber: 'AbstractUser', author: 'AbstractUser'
    ) -> Subscription:
        """
        Создать подписку от подписчика на автора.

        Аргументы:
            subscriber: Пользователь, который хочет подписаться.
            author: Пользователь, на которого подписываются.

        Возвращает:
            Subscription: Созданный экземпляр подписки.

        Вызывает:
            ValidationError: Если подписка уже существует или
                            пользователь пытается подписаться на себя.
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
        Удалить подписку от подписчика на автора.

        Аргументы:
            subscriber: Пользователь, который хочет отписаться.
            author: Пользователь, от которого отписываются.

        Вызывает:
            Http404: Если подписка не существует.
        """
        from django.shortcuts import get_object_or_404
        get_object_or_404(
            Subscription, author=author, subscriber=subscriber
        ).delete()

    @staticmethod
    def get_subscriptions_queryset(user: 'AbstractUser') -> QuerySet:
        """
        Получить queryset пользователей, на которых подписан данный
        пользователь.

        Аргументы:
            user: Пользователь, для которого получить подписки.

        Возвращает:
            QuerySet экземпляров User.
        """
        return User.objects.filter(authors__subscriber=user)


class RecipeInteractionProvider:
    """Сервис для управления взаимодействиями с рецептами
    (избранное, корзина)."""

    @staticmethod
    def add_to_favorites(
        user: 'AbstractUser', recipe: Recipe
    ) -> Favorite:
        """
        Добавить рецепт в избранное пользователя.

        Аргументы:
            user: Пользователь, который хочет добавить рецепт.
            recipe: Рецепт для добавления в избранное.

        Возвращает:
            Favorite: Созданный экземпляр избранного.

        Вызывает:
            ValidationError: Если рецепт уже в избранном.
        """
        favorite, created = Favorite.objects.get_or_create(
            user=user, recipe=recipe
        )
        if not created:
            raise ValidationError(dict(error=Error.ALREADY_FAVORITED))
        return favorite

    @staticmethod
    def remove_from_favorites(
        user: 'AbstractUser', recipe: Recipe
    ) -> None:
        """
        Удалить рецепт из избранного пользователя.

        Аргументы:
            user: Пользователь, который хочет удалить рецепт.
            recipe: Рецепт для удаления из избранного.

        Вызывает:
            Http404: Если избранное не существует.
        """
        from django.shortcuts import get_object_or_404
        get_object_or_404(Favorite, user=user, recipe=recipe).delete()

    @staticmethod
    def add_to_shopping_cart(
        user: 'AbstractUser', recipe: Recipe
    ) -> ShoppingCart:
        """
        Добавить рецепт в список покупок пользователя.

        Аргументы:
            user: Пользователь, который хочет добавить рецепт.
            recipe: Рецепт для добавления в список покупок.

        Возвращает:
            ShoppingCart: Созданный экземпляр элемента списка покупок.

        Вызывает:
            ValidationError: Если рецепт уже в списке покупок.
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
        Удалить рецепт из списка покупок пользователя.

        Аргументы:
            user: Пользователь, который хочет удалить рецепт.
            recipe: Рецепт для удаления из списка покупок.

        Вызывает:
            Http404: Если элемент списка покупок не существует.
        """
        from django.shortcuts import get_object_or_404
        get_object_or_404(
            ShoppingCart, user=user, recipe=recipe
        ).delete()
