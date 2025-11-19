"""Модели рецептов."""

from secrets import choice as secure_choice

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import IntegrityError, models

from . import constants as const


User = get_user_model()


def generate_short_code(length: int = const.SHORT_CODE_LENGTH):
    """Генерирует случайный короткий код для рецепта."""
    return ''.join(
        secure_choice(const.SHORT_CODE_ALPHABET) for _ in range(length)
    )


class Tag(models.Model):

    """Тег для категоризации рецептов."""

    slug = models.SlugField(
        'Слаг', max_length=const.TAG_SLUG_MAX_LENGTH, unique=True
    )
    name = models.CharField(
        'Название',
        max_length=const.CHAR_MAX_LENGTH,
        unique=True,
        db_index=True,
    )

    class Meta:

        """Метаданные модели."""

        ordering = ('name',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        """Возвращает строковое представление тега."""
        return self.name


class Ingredient(models.Model):

    """Ингредиент для использования в рецептах."""

    name = models.CharField('Название', max_length=const.CHAR_MAX_LENGTH)
    measurement_unit = models.CharField(
        'Единица измерения', max_length=const.CHAR_MAX_LENGTH
    )

    class Meta:

        """Метаданные модели."""

        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        """Возвращает строковое представление ингредиента."""
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):

    """Рецепт с ингредиентами и тегами."""

    name = models.CharField('Название', max_length=const.CHAR_MAX_LENGTH)
    text = models.TextField('Описание')
    image = models.ImageField(
        'Изображение', upload_to=settings.RECIPES_IMAGES_PATH
    )
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления (мин)',
        validators=[
            MinValueValidator(
                const.RECIPE_COOKING_MINIMUM, const.RECIPE_COOKING_ERROR
            )
        ],
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор',
    )
    tags = models.ManyToManyField(
        Tag, related_name='recipes', verbose_name='Теги'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name='Ингредиенты',
    )
    short_url_code = models.SlugField(
        'Короткий код',
        max_length=const.SHORT_CODE_LENGTH,
        unique=True,
        blank=True,
    )
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)

    class Meta:

        """Метаданные модели."""

        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        """Возвращает строковое представление рецепта."""
        return self.name

    def save(self, *args, **kwargs):
        """Сохраняет рецепт с генерацией короткого кода."""
        if not self.short_url_code:
            self.short_url_code = generate_short_code()

        max_attempts = 30
        for _ in range(max_attempts):
            try:
                super().save(*args, **kwargs)
                return
            except IntegrityError:
                self.short_url_code = generate_short_code()

        message = f'Не удалось сгенерировать код за {max_attempts} попыток.'
        raise IntegrityError(message)


class RecipeIngredient(models.Model):

    """Связь между рецептом и ингредиентом с количеством."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
    )
    amount = models.PositiveSmallIntegerField(
        'Количество',
        validators=[
            MinValueValidator(
                const.INGREDIENT_AMOUNT_MINIMUM, const.INGREDIENT_AMOUNT_ERROR
            )
        ],
    )

    class Meta:

        """Метаданные модели."""

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

    def __str__(self):
        """Возвращает строковое представление связи."""
        return f'{self.recipe} - {self.ingredient}'


class UserRecipeRelation(models.Model):

    """Абстрактная модель связи пользователя с рецептом."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='%(class)s_set',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='%(class)ss',
        verbose_name='Рецепт',
    )

    class Meta:

        """Метаданные модели."""

        abstract = True
        ordering = ('user', 'recipe')

    def __str__(self):
        """Возвращает строковое представление связи."""
        return f'{self.user} - {self.recipe}'


class Favorite(UserRecipeRelation):

    """Избранный рецепт пользователя."""

    class Meta(UserRecipeRelation.Meta):

        """Метаданные модели."""

        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite',
            )
        ]


class ShoppingCart(UserRecipeRelation):

    """Рецепт в списке покупок пользователя."""

    class Meta(UserRecipeRelation.Meta):

        """Метаданные модели."""

        verbose_name = 'Корзина покупок'
        verbose_name_plural = 'Корзина покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_cart',
            )
        ]
