"""Модели для управления аккаунтами и социальными функциями."""
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.constraints import UniqueConstraint

from .constants import DisplayNames, FieldConstraints
from .validators import validate_account_username


class Account(AbstractUser):
    """
    Расширенная модель пользовательского аккаунта с поддержкой фото профиля.

    Использует email как основной идентификатор для аутентификации,
    при этом сохраняет username для отображения.
    """
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    email = models.EmailField(
        verbose_name=DisplayNames.EMAIL,
        max_length=FieldConstraints.EMAIL_MAX_LENGTH,
        unique=True,
        help_text='Основной идентификатор для аутентификации аккаунта.'
    )
    username = models.CharField(
        verbose_name=DisplayNames.USERNAME,
        max_length=FieldConstraints.USERNAME_MAX_LENGTH,
        unique=True,
        validators=(validate_account_username,),
        help_text='Уникальное отображаемое имя для аккаунта.'
    )
    first_name = models.CharField(
        verbose_name=DisplayNames.FIRST_NAME,
        max_length=FieldConstraints.FIRST_NAME_MAX_LENGTH,
        help_text='Имя владельца аккаунта.'
    )
    last_name = models.CharField(
        verbose_name=DisplayNames.LAST_NAME,
        max_length=FieldConstraints.LAST_NAME_MAX_LENGTH,
        help_text='Фамилия владельца аккаунта.'
    )
    profile_picture = models.ImageField(
        verbose_name=DisplayNames.PROFILE_PICTURE,
        null=True,
        blank=True,
        upload_to=settings.AVATARS_PATH,
        help_text='Необязательное фото профиля для аккаунта.'
    )

    class Meta(AbstractUser.Meta):
        verbose_name = DisplayNames.ACCOUNT
        verbose_name_plural = DisplayNames.ACCOUNTS
        ordering = ('username',)
        db_table = 'accounts_account'

    def __str__(self) -> str:
        """Возвращает username как строковое представление."""
        return self.username


class FollowRelationship(models.Model):
    """
    Представляет отношение подписки между двумя аккаунтами.

    Отслеживает, когда один аккаунт подписывается на другой, обеспечивая
    социальные функции, такие как агрегация ленты и обнаружение контента.
    """
    follower = models.ForeignKey(
        to=Account,
        verbose_name=DisplayNames.FOLLOWER,
        related_name='following_relationships',
        on_delete=models.CASCADE,
        help_text='Аккаунт, который подписывается.'
    )
    following = models.ForeignKey(
        to=Account,
        verbose_name=DisplayNames.FOLLOWING,
        related_name='follower_relationships',
        on_delete=models.CASCADE,
        help_text='Аккаунт, на который подписываются.'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='Временная метка создания отношения подписки.'
    )

    class Meta:
        verbose_name = DisplayNames.FOLLOW_RELATIONSHIP
        verbose_name_plural = DisplayNames.FOLLOW_RELATIONSHIPS
        ordering = ('-created_at',)
        constraints = (
            UniqueConstraint(
                fields=('follower', 'following'),
                name='unique_follow_relationship'
            ),
        )
        db_table = 'accounts_followrelationship'

    def __str__(self) -> str:
        """Возвращает человекочитаемое представление."""
        return f'{self.follower} follows {self.following}'
