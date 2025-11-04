"""
Валидирующие схемы для API приложения Foodgram.

Модуль содержит сериализаторы для преобразования экземпляров моделей
в/из JSON с валидацией и бизнес-логикой.
"""
from collections import Counter
from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import transaction
from djoser.serializers import UserSerializer as DjoserUserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.constants import Error, MinValue
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Subscription,
    Tag,
)

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser

User = get_user_model()


class UserSerializer(DjoserUserSerializer):
    """
    Сериализатор пользователя со статусом подписки.

    Расширяет сериализатор Djoser для включения аватара и
    статуса подписки текущего пользователя.
    """
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            *DjoserUserSerializer.Meta.fields, 'avatar', 'is_subscribed'
        )

    def get_is_subscribed(self, author: 'AbstractUser') -> bool:
        """
        Проверить, подписан ли текущий пользователь на этого автора.

        Использует предварительно загруженные данные, если доступны,
        для избежания N+1 запросов.
        """
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False

        user = request.user

        # Оптимизированная проверка - в будущем может быть
        # предварительно загружена. Сейчас прямой запрос приемлем,
        # так как вызывается один раз для пользователя

        return Subscription.objects.filter(
            author=author, subscriber=user
        ).exists()


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для загрузки аватара пользователя."""
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для категории/тега блюда."""
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиента/компонента."""
    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для связи блюда с ингредиентом и количеством."""
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source='ingredient'
    )
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit',
    )
    amount = serializers.IntegerField(
        validators=[
            MinValueValidator(
                limit_value=MinValue.AMOUNT, message=Error.AMOUNT
            )
        ]
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class ReadRecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для чтения данных блюда с полными деталями.

    Включает категории, автора, ингредиенты и флаги взаимодействия
    пользователя. Оптимизирован для минимизации запросов БД.
    """
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        source='recipeingredients', many=True, read_only=True
    )
    is_in_shopping_cart = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
            'is_in_shopping_cart',
            'is_favorited',
        )
        read_only_fields = fields

    def get_is_in_shopping_cart(self, recipe: Recipe) -> bool:
        """
        Проверить, находится ли блюдо в списке покупок пользователя.

        Использует предварительно загруженные данные, если доступны,
        для избежания N+1 запросов.
        """
        user = self.context.get('request').user
        if not user.is_authenticated:
            return False

        # Проверяем наличие предварительно загруженных данных
        if hasattr(recipe, '_user_shopping_carts'):
            return len(recipe._user_shopping_carts) > 0

        return ShoppingCart.objects.filter(
            user=user, recipe=recipe
        ).exists()

    def get_is_favorited(self, recipe: Recipe) -> bool:
        """
        Проверить, находится ли блюдо в избранном у пользователя.

        Использует предварительно загруженные данные, если доступны,
        для избежания N+1 запросов.
        """
        user = self.context.get('request').user
        if not user.is_authenticated:
            return False

        # Проверяем наличие предварительно загруженных данных
        if hasattr(recipe, '_user_favorites'):
            return len(recipe._user_favorites) > 0

        return Favorite.objects.filter(user=user, recipe=recipe).exists()


class WriteRecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания и обновления блюд.

    Обрабатывает создание/обновление блюда с вложенными
    ингредиентами и категориями. Валидирует на дубликаты и
    обеспечивает наличие всех обязательных полей.
    """
    ingredients = serializers.ListField(
        child=RecipeIngredientSerializer(),
        allow_empty=False,
        required=True,
    )
    tags = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(
            queryset=Tag.objects.all(),
        ),
        allow_empty=False,
        required=True,
    )
    image = Base64ImageField(allow_empty_file=False, required=True)

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
        )

    @staticmethod
    def _check_duplicates(array: list, field_name: str) -> None:
        """
        Проверить дубликаты в массиве и вызвать ошибку валидации.

        Аргументы:
            array: Список значений для проверки дубликатов.
            field_name: Имя поля для сообщения об ошибке.

        Вызывает:
            ValidationError: Если найдены дубликаты.
        """
        counts = Counter(array)
        duplicates = {item for item, count in counts.items()
                      if count > 1}
        if duplicates:
            raise serializers.ValidationError(
                {field_name: Error.DUPLICATES.format(duplicates)}
            )

    def validate_tags(self, tags: list) -> list:
        """
        Валидировать список категорий на дубликаты.

        Аргументы:
            tags: Список экземпляров Tag.

        Возвращает:
            Валидированный список категорий.

        Вызывает:
            ValidationError: Если найдены дубликаты категорий.
        """
        self._check_duplicates([tag.id for tag in tags], 'tags')
        return tags

    def validate_ingredients(self, ingredients: list) -> list:
        """
        Валидировать список ингредиентов на дубликаты.

        Аргументы:
            ingredients: Список словарей ингредиентов.

        Возвращает:
            Валидированный список ингредиентов.

        Вызывает:
            ValidationError: Если найдены дубликаты ингредиентов.
        """
        self._check_duplicates(
            [item['ingredient'].id for item in ingredients],
            'ingredients',
        )
        return ingredients

    def validate_image(self, image) -> object:
        """
        Валидировать наличие изображения.

        Аргументы:
            image: Объект файла изображения.

        Возвращает:
            Валидированное изображение.

        Вызывает:
            ValidationError: Если изображение пусто.
        """
        if not image:
            raise serializers.ValidationError(Error.NO_IMAGE)
        return image

    @staticmethod
    def _save_ingredients(recipe: Recipe, ingredients: list) -> None:
        """
        Сохранить ингредиенты блюда, используя bulk_create для
        эффективности.

        Аргументы:
            recipe: Экземпляр блюда, к которому нужно прикрепить
                    ингредиенты.
            ingredients: Список словарей ингредиентов с ключами:
                        ingredient, amount
        """
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient['ingredient'],
                amount=ingredient['amount'],
            )
            for ingredient in ingredients
        )

    @transaction.atomic
    def create(self, validated_data: dict) -> Recipe:
        """
        Создать блюдо с ингредиентами и категориями.

        Аргументы:
            validated_data: Валидированные данные блюда.

        Возвращает:
            Созданный экземпляр Recipe.
        """
        ingredients_data = validated_data.pop('ingredients')
        recipe = super().create(validated_data)
        self._save_ingredients(recipe, ingredients_data)
        return recipe

    @transaction.atomic
    def update(self, recipe: Recipe, validated_data: dict) -> Recipe:
        """
        Обновить блюдо, опционально обновляя ингредиенты.

        Аргументы:
            recipe: Экземпляр блюда для обновления.
            validated_data: Валидированные данные блюда.

        Возвращает:
            Обновленный экземпляр Recipe.
        """
        try:
            new_ingredients = validated_data.pop('ingredients')
            recipe.ingredients.clear()
            self._save_ingredients(recipe, new_ingredients)
        except KeyError:
            # Ингредиенты не предоставлены, сохраняем существующие
            pass
        return super().update(recipe, validated_data)

    def to_representation(self, recipe: Recipe) -> dict:
        """
        Преобразовать экземпляр блюда в сериализованное представление.

        Использует ReadRecipeSerializer для согласованного формата
        вывода.

        Аргументы:
            recipe: Экземпляр блюда.

        Возвращает:
            Сериализованные данные блюда.
        """
        return ReadRecipeSerializer(recipe, context=self.context).data


class ShortRecipeSerializer(serializers.ModelSerializer):
    """
    Минимальный сериализатор блюда для вложенных представлений.

    Используется в подписках и других местах, где полные данные блюда
    не требуются.
    """

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )


class ReadSubscriptionSerializer(UserSerializer):
    """
    Сериализатор для данных подписки пользователя.

    Расширяет UserSerializer для включения рецептов пользователя с
    поддержкой лимита.
    """
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(source='recipes.count')

    class Meta(UserSerializer.Meta):
        fields = (
            *UserSerializer.Meta.fields, 'recipes', 'recipes_count'
        )

    def get_recipes(self, user: 'AbstractUser') -> list:
        """
        Получить рецепты пользователя с опциональным лимитом.

        Аргументы:
            user: Экземпляр пользователя для получения рецептов.

        Возвращает:
            Список словарей сериализованных рецептов.
        """
        limit = int(
            self.context.get('request').GET.get('recipes_limit', 10**10)
        )
        recipes = user.recipes.all()[:limit]
        return ShortRecipeSerializer(
            recipes,
            context=self.context,
            many=True,
        ).data
