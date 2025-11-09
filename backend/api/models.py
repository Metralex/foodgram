from secrets import choice as secure_choice
from string import ascii_letters, digits

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import IntegrityError, models
from django.db.models import Q

from .validators import validate_username


CODE_LENGTH = 6
MAX_GENERATION_ATTEMPTS = 30
ALLOWED_CHARS = ascii_letters + digits


class Tag(models.Model):
    """Представляет тематическую категорию для кулинарных рецептов."""
    
    slug = models.SlugField(
        'Уникальный слаг',
        max_length=200,
        unique=True,
        db_index=True,
    )
    name = models.CharField('Название', max_length=200, unique=True)

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Представляет продукт для приготовления блюд."""
    
    measurement_unit = models.CharField('Единица измерения', max_length=200)
    name = models.CharField('Название', max_length=200)

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class User(AbstractUser):
    """Расширенная модель пользователя системы."""
    
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
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username
    
    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'


class Recipe(models.Model):
    """Кулинарный рецепт с описанием, ингредиентами и временем готовки."""
    
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)
    short_url_code = models.SlugField(
        'Короткий код',
        max_length=CODE_LENGTH,
        unique=True,
        blank=True,
        db_index=True,
    )
    cooking_time = models.PositiveIntegerField(
        'Время приготовления (в минутах)',
        validators=[MinValueValidator(1, 'Минимум 1 минута')],
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
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
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.name
    
    @classmethod
    def _generate_unique_code(cls, attempts=MAX_GENERATION_ATTEMPTS):
        """Генерирует уникальный короткий код для рецепта."""
        for _ in range(attempts):
            generated_code = ''.join(
                secure_choice(ALLOWED_CHARS) for _ in range(CODE_LENGTH)
            )
            if not cls.objects.filter(short_url_code=generated_code).exists():
                return generated_code
        return None
    
    def _ensure_short_url_code(self):
        """Обеспечивает наличие короткого кода перед сохранением."""
        if not self.short_url_code:
            generated_code = self._generate_unique_code()
            if generated_code:
                self.short_url_code = generated_code
    
    def save(self, *args, **kwargs):
        self._ensure_short_url_code()
        attempt_count = 0
        while attempt_count < MAX_GENERATION_ATTEMPTS:
            try:
                super().save(*args, **kwargs)
                break
            except IntegrityError:
                attempt_count += 1
                self.short_url_code = self._generate_unique_code()
                if not self.short_url_code:
                    raise


class RecipeIngredient(models.Model):
    """Связывает рецепт с конкретным количеством ингредиента."""
    
    amount = models.PositiveIntegerField(
        'Количество',
        validators=[MinValueValidator(1, 'Минимум 1')],
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
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецепта'
        default_related_name = '%(class)ss'
        ordering = ('recipe', 'ingredient')
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            )
        ]

    def __str__(self):
        return f'{self.recipe} - {self.ingredient}'


class Subscription(models.Model):
    """Хранит информацию о подписке одного пользователя на другого."""
    
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
                name='unique_subscription'
            ),
            models.CheckConstraint(
                check=~Q(subscriber=models.F('author')),
                name='prevent_self_subscription'
            ),
        ]

    def __str__(self):
        return f'{self.subscriber} подписан на {self.author}'


class Favorite(models.Model):
    """Отмечает рецепты, добавленные пользователем в избранное."""
    
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
                name='unique_favorite'
            )
        ]

    def __str__(self):
        return f'{self.user} - {self.recipe}'


class ShoppingCart(models.Model):
    """Представляет список покупок пользователя на основе рецептов."""
    
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
                name='unique_shopping_cart'
            )
        ]

    def __str__(self):
        return f'{self.user} - {self.recipe}'
