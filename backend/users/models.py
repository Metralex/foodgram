"""Модели пользователей."""

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import F, Q
from users.constants import (
    EMAIL_MAX_LENGTH,
    NAME_MAX_LENGTH,
    USERNAME_MAX_LENGTH,
)

from .validators import validate_username


class User(AbstractUser):

    """Кастомная модель пользователя с поддержкой аватара."""

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    email = models.EmailField(
        'Email', max_length=EMAIL_MAX_LENGTH, unique=True
    )
    username = models.CharField(
        'Имя пользователя',
        max_length=USERNAME_MAX_LENGTH,
        unique=True,
        validators=[validate_username],
    )
    first_name = models.CharField('Имя', max_length=NAME_MAX_LENGTH)
    last_name = models.CharField('Фамилия', max_length=NAME_MAX_LENGTH)
    avatar = models.ImageField(
        'Аватар',
        upload_to=settings.AVATARS_PATH,
        blank=True,
    )

    class Meta:

        """Метаданные модели."""

        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        """Возвращает строковое представление пользователя."""
        return self.username

    @property
    def full_name(self):
        """Возвращает полное имя пользователя."""
        return f'{self.first_name} {self.last_name}'.strip()


class Subscription(models.Model):

    """Подписка пользователя на автора."""

    subscriber = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='authors',
        verbose_name='Автор',
    )

    class Meta:

        """Метаданные модели."""

        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['subscriber', 'author'],
                name='unique_subscription',
            ),
            models.CheckConstraint(
                check=~Q(subscriber=F('author')),
                name='prevent_self_subscription',
            ),
        ]

    def __str__(self):
        """Возвращает строковое представление подписки."""
        return f'{self.subscriber} -> {self.author}'
