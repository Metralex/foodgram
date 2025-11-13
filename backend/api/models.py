from __future__ import annotations

from secrets import choice as secure_choice
from string import ascii_letters, digits

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import IntegrityError, models
from django.db.models import F, Q

from .validators import validate_username

__all__ = (
    'Tag',
    'Ingredient',
    'User',
    'Recipe',
    'RecipeIngredient',
    'Subscription',
    'Favorite',
    'ShoppingCart',
)


# --------------------------------------------------------------------------- #
# Configuration constants
# --------------------------------------------------------------------------- #
SHORT_CODE_LENGTH = 6
SHORT_CODE_ALPHABET = ascii_letters + digits
RECIPE_COOKING_MINIMUM = 1
RECIPE_COOKING_ERROR = 'Минимум 1 минута'
INGREDIENT_AMOUNT_MINIMUM = 1
INGREDIENT_AMOUNT_ERROR = 'Минимум 1'

# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #


def generate_short_code(length: int = SHORT_CODE_LENGTH) -> str:
    """Генерирует случайный короткий код."""
    return "".join(secure_choice(SHORT_CODE_ALPHABET) for _ in range(length))


# --------------------------------------------------------------------------- #
# Domain models
# --------------------------------------------------------------------------- #
class Tag(models.Model):
    """Represents a thematic tag used to group recipes."""

    slug = models.SlugField(
        'Уникальный слаг',
        max_length=200,
        unique=True,
        db_index=True,
    )
    name = models.CharField('Название', max_length=200, unique=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self) -> str:
        return self.name


class Ingredient(models.Model):
    """Stores products used for recipe preparation."""

    measurement_unit = models.CharField('Единица измерения', max_length=200)
    name = models.CharField('Название', max_length=200)

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self) -> str:
        return f"{self.name}, {self.measurement_unit}"


class User(AbstractUser):
    """Custom user model supporting email login and profile avatars."""

    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    USERNAME_FIELD = 'email'

    last_name = models.CharField('Фамилия', max_length=150)
    first_name = models.CharField('Имя', max_length=150)
    username = models.CharField(
        'Имя пользователя',
        max_length=150,
        unique=True,
        validators=[validate_username],
    )
    email = models.EmailField(
        'Электронная почта',
        max_length=254,
        unique=True,
        db_index=True,
    )
    avatar = models.ImageField(
        'Фото профиля',
        upload_to=settings.AVATARS_PATH,
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self) -> str:
        return self.username

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


class Recipe(models.Model):
    """Culinary recipe with tags, ingredients and preparation metadata."""

    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)
    short_url_code = models.SlugField(
        'Короткий код',
        max_length=SHORT_CODE_LENGTH,
        unique=True,
        blank=True,
        db_index=True,
    )
    cooking_time = models.PositiveIntegerField(
        'Время приготовления (в минутах)',
        validators=[
            MinValueValidator(RECIPE_COOKING_MINIMUM, RECIPE_COOKING_ERROR)
        ],
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги',
    )
    ingredients = models.ManyToManyField(
        'Ingredient',
        through="RecipeIngredient",
        related_name='recipes',
        verbose_name='Ингредиенты',
    )
    text = models.TextField('Описание')
    image = models.ImageField(
        'Картинка',
        upload_to=settings.RECIPES_IMAGES_PATH,
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор',
    )
    name = models.CharField('Название', max_length=200)

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None:  # type: ignore[override]
        """При сохранении генерирует уникальный короткий код."""
        if not self.short_url_code:
            self.short_url_code = generate_short_code()

        # Попытка сохранить с уникальным кодом
        max_attempts = 30
        for _ in range(max_attempts):
            try:
                super().save(*args, **kwargs)
                return
            except IntegrityError:
                self.short_url_code = generate_short_code()

        raise IntegrityError(
            f"Не удалось сгенерировать уникальный код "
            f"за {max_attempts} попыток."
        )


class RecipeIngredient(models.Model):
    """Intermediate model linking recipes with ingredient amounts."""

    amount = models.PositiveIntegerField(
        'Количество',
        validators=[
            MinValueValidator(
                INGREDIENT_AMOUNT_MINIMUM, INGREDIENT_AMOUNT_ERROR
            )
        ],
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    class Meta:
        ordering = ('recipe', 'ingredient')
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецепта'
        default_related_name = '%(class)ss'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient',
            )
        ]

    def __str__(self) -> str:
        return f"{self.recipe} - {self.ingredient}"


class Subscription(models.Model):
    """Represents a follower relationship between users."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='authors',
        verbose_name='Автор',
    )
    subscriber = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='Подписчик',
    )

    class Meta:
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

    def __str__(self) -> str:
        return f"{self.subscriber} подписан на {self.author}"


class Favorite(models.Model):
    """Tracks recipes a user has marked as favourites."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Рецепт',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь',
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite',
            )
        ]

    def __str__(self) -> str:
        return f"{self.user} - {self.recipe}"


class ShoppingCart(models.Model):
    """Stores recipes added to a user's shopping cart."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shoppingcarts',
        verbose_name='Рецепт',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь',
    )

    class Meta:
        verbose_name = 'Корзина покупок'
        verbose_name_plural = 'Корзина покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_cart',
            )
        ]

    def __str__(self) -> str:
        return f"{self.user} - {self.recipe}"
