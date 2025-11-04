from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import IntegrityError, models
from django.db.models.constraints import UniqueConstraint
from django.urls import reverse

from .constants import (
    Error,
    FieldLength,
    MinValue,
    VerboseName,
    VerboseNamePlural,
)
from .services import ShortUrlCodeGenerator
from .validators import validate_username


class User(AbstractUser):

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    email = models.EmailField(
        verbose_name=VerboseName.EMAIL,
        max_length=FieldLength.EMAIL,
        unique=True,
    )
    username = models.CharField(
        verbose_name=VerboseName.USERNAME,
        max_length=FieldLength.USERNAME,
        unique=True,
        validators=(validate_username,),
    )
    first_name = models.CharField(
        verbose_name=VerboseName.FIRST_NAME, max_length=FieldLength.FIRST_NAME
    )
    last_name = models.CharField(
        verbose_name=VerboseName.LAST_NAME, max_length=FieldLength.LAST_NAME
    )
    avatar = models.ImageField(
        verbose_name=VerboseName.AVATAR,
        null=True,
        blank=True,
        upload_to=settings.AVATARS_PATH,
    )

    class Meta(AbstractUser.Meta):
        verbose_name = VerboseName.USER
        verbose_name_plural = VerboseNamePlural.USERS
        ordering = ('username',)

    def __str__(self) -> str:
        return self.username


class Subscription(models.Model):
    subscriber = models.ForeignKey(
        to=User,
        verbose_name=VerboseName.SUBSCRIBER,
        related_name='subscribers',
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        to=User,
        verbose_name=VerboseName.AUTHOR,
        related_name='authors',
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = VerboseName.SUBSCRIPTION
        verbose_name_plural = VerboseNamePlural.SUBSCRIPTIONS
        ordering = ('author',)
        constraints = (
            UniqueConstraint(
                fields=('subscriber', 'author'), name='unique_%(class)s'
            ),
        )

    def __str__(self) -> str:
        return f'{self.subscriber} подписан на {self.author}'


class Tag(models.Model):
    name = models.CharField(
        verbose_name=VerboseName.NAME,
        max_length=FieldLength.TAG,
    )

    slug = models.SlugField(
        verbose_name=VerboseName.SLUG,
        max_length=FieldLength.TAG,
        null=True,
        unique=True,
    )

    class Meta:
        verbose_name = VerboseName.TAG
        verbose_name_plural = VerboseNamePlural.TAGS
        default_related_name = '%(class)ss'
        ordering = ('name',)

    def __str__(self) -> str:
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        verbose_name=VerboseName.NAME,
        max_length=FieldLength.INGREDIENT,
    )
    measurement_unit = models.CharField(
        verbose_name=VerboseName.MEASUREMENT_UNIT,
        max_length=FieldLength.MEASUREMENT_UNIT,
    )

    class Meta:
        verbose_name = VerboseName.INGREDIENT
        verbose_name_plural = VerboseNamePlural.INGREDIENTS
        default_related_name = '%(class)ss'
        ordering = ('name',)

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class Recipe(models.Model):
    """
    Recipe model representing a cooking recipe with ingredients and tags.

    Automatically generates a unique short URL code on save if not provided.
    """

    name = models.CharField(
        verbose_name=VerboseName.NAME,
        max_length=FieldLength.RECIPE_NAME,
    )
    tags = models.ManyToManyField(to=Tag, verbose_name=VerboseNamePlural.TAGS)
    ingredients = models.ManyToManyField(
        to=Ingredient,
        through='RecipeIngredient',
        verbose_name=VerboseNamePlural.INGREDIENTS,
    )
    author = models.ForeignKey(
        to=User, on_delete=models.CASCADE, verbose_name=VerboseName.AUTHOR
    )
    image = models.ImageField(
        verbose_name=VerboseName.IMAGE,
        upload_to=settings.RECIPES_IMAGES_PATH,
    )
    text = models.TextField(verbose_name=VerboseName.TEXT)
    cooking_time = models.PositiveIntegerField(
        verbose_name=VerboseName.COOKING_TIME,
        validators=[
            MinValueValidator(
                limit_value=MinValue.COOKING_TIME,
                message=Error.COOKING_TIME,
            )
        ],
    )
    short_url_code = models.SlugField(
        verbose_name=VerboseName.SHORT_URL_CODE,
        max_length=FieldLength.SHORT_URL_CODE,
        unique=True,
    )
    pub_date = models.DateTimeField(
        verbose_name=VerboseName.PUB_DATE, auto_now_add=True
    )

    class Meta:
        verbose_name = VerboseName.RECIPE
        verbose_name_plural = VerboseNamePlural.RECIPES
        default_related_name = '%(class)ss'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        """Получить абсолютный URL для детального просмотра рецепта."""
        return reverse('recipes:short_link', args=[self.pk])

    def save(self, *args, **kwargs):
        """
        Сохранить экземпляр рецепта, обеспечив уникальность кода
        короткой ссылки.

        Если код не установлен, генерирует уникальный код с использованием
        сервиса ShortUrlCodeGenerator. Обрабатывает IntegrityError путём
        регенерации кода при возникновении коллизии.
        """
        if not self.short_url_code:
            ShortUrlCodeGenerator.ensure_unique_code(self)

        attempts = 0
        while attempts < ShortUrlCodeGenerator.MAX_ATTEMPTS:
            try:
                super().save(*args, **kwargs)
                break
            except IntegrityError as e:
                # Повторяем только если ошибка касается уникальности
                # short_url_code
                if 'short_url_code' in str(e):
                    attempts += 1
                    if attempts >= ShortUrlCodeGenerator.MAX_ATTEMPTS:
                        raise RuntimeError(Error.SHORT_URL_CODE_GEN)
                    self.short_url_code = ShortUrlCodeGenerator.generate_code()
                else:
                    raise


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        to=Recipe,
        on_delete=models.CASCADE,
        verbose_name=VerboseName.RECIPE,
    )
    ingredient = models.ForeignKey(
        to=Ingredient,
        on_delete=models.CASCADE,
        verbose_name=VerboseName.INGREDIENT,
    )
    amount = models.PositiveIntegerField(
        verbose_name=VerboseName.AMOUNT,
        validators=[
            MinValueValidator(
                limit_value=MinValue.AMOUNT,
                message=Error.AMOUNT,
            )
        ],
    )

    class Meta:
        default_related_name = '%(class)ss'
        ordering = ('recipe', 'ingredient')
        constraints = (
            UniqueConstraint(
                fields=('recipe', 'ingredient'), name='unique_%(class)s'
            ),
        )
        verbose_name = VerboseName.RECIPE_INGREDIENT
        verbose_name_plural = VerboseNamePlural.RECIPE_INGREDIENTS

    def __str__(self) -> str:
        return f'Ингредиент {self.ingredient} для рецепта {self.recipe}'


class BaseUserRecipeModel(models.Model):
    user = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        to=Recipe,
        on_delete=models.CASCADE,
        verbose_name=VerboseName.RECIPE,
    )

    class Meta:
        abstract = True
        ordering = ('recipe',)
        default_related_name = '%(class)ss'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_%(class)s',
            ),
        ]


class Favorite(BaseUserRecipeModel):
    class Meta(BaseUserRecipeModel.Meta):
        verbose_name = VerboseName.FAVORITE
        verbose_name_plural = VerboseNamePlural.FAVORITES


class ShoppingCart(BaseUserRecipeModel):
    class Meta(BaseUserRecipeModel.Meta):
        verbose_name = VerboseName.SHOPPING_CART
        verbose_name_plural = VerboseNamePlural.SHOPPING_CARTS
