"""Реализация паттерна Repository для бизнес-логики аккаунтов."""
from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from rest_framework.exceptions import ValidationError

from .models import FollowRelationship

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser

Account = get_user_model()


class FollowRepository:
    """Репозиторий для управления отношениями подписки."""

    @staticmethod
    def create_follow(
        follower: 'AbstractUser', following: 'AbstractUser'
    ) -> FollowRelationship:
        """
        Создает отношение подписки между двумя аккаунтами.

        Args:
            follower: Аккаунт, который хочет подписаться.
            following: Аккаунт, на который подписываются.

        Returns:
            Созданный экземпляр FollowRelationship.

        Raises:
            ValidationError: При попытке подписаться на себя или
                если уже подписан.
        """
        if follower == following:
            raise ValidationError(
                {'error': 'Cannot follow your own account.'}
            )

        relationship, created = FollowRelationship.objects.get_or_create(
            follower=follower, following=following
        )
        if not created:
            raise ValidationError(
                {'error': 'Already following this account.'}
            )

        return relationship

    @staticmethod
    def delete_follow(
        follower: 'AbstractUser', following: 'AbstractUser'
    ) -> None:
        """
        Удаляет отношение подписки.

        Args:
            follower: Аккаунт, который хочет отписаться.
            following: Аккаунт, от которого отписываются.

        Raises:
            Http404: Если отношение не существует.
        """
        from django.shortcuts import get_object_or_404
        get_object_or_404(
            FollowRelationship,
            follower=follower,
            following=following
        ).delete()

    @staticmethod
    def get_following_queryset(account: 'AbstractUser') -> QuerySet:
        """
        Получает queryset аккаунтов, на которые подписан данный аккаунт.

        Args:
            account: Аккаунт, для которого получить список подписок.

        Returns:
            QuerySet экземпляров Account, на которые подписан аккаунт.
        """
        return Account.objects.filter(
            follower_relationships__follower=account
        ).distinct()

    @staticmethod
    def is_following(
        follower: 'AbstractUser', following: 'AbstractUser'
    ) -> bool:
        """
        Проверяет, подписан ли один аккаунт на другой.

        Args:
            follower: Потенциальный подписчик.
            following: Потенциальный аккаунт для подписки.

        Returns:
            True если подписан, False в противном случае.
        """
        if not follower.is_authenticated:
            return False
        return FollowRelationship.objects.filter(
            follower=follower,
            following=following
        ).exists()
