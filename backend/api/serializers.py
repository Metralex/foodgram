"""Сериализаторы для API Foodgram."""

from __future__ import annotations

from typing import Any, Dict, List

from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from djoser.serializers import UserSerializer as DjoserUserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from .models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Subscription,
    Tag,
)
from .services import RecipeService

User = get_user_model()

# --------------------------------------------------------------------------- #
# Validation constants
# --------------------------------------------------------------------------- #
DUPLICATE_ERROR_MSG = 'Обнаружены дублирующиеся элементы: {}'
EMPTY_IMAGE_ERROR = 'Изображение не может отсутствовать'
MIN_INGREDIENT_AMOUNT = 1
MIN_AMOUNT_ERROR = f'Количество должно быть не менее {MIN_INGREDIENT_AMOUNT}'


# --------------------------------------------------------------------------- #
# Basic resource serializers
# --------------------------------------------------------------------------- #
class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов рецептов."""

    class Meta:
        model = Tag
        fields = '__all__'
        read_only_fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""

    class Meta:
        model = Ingredient
        fields = '__all__'
        read_only_fields = ('id', 'name', 'measurement_unit')


# --------------------------------------------------------------------------- #
# User-related serializers
# --------------------------------------------------------------------------- #
class UserSerializer(DjoserUserSerializer):
    """Сериализатор пользователя с информацией о подписке."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (*DjoserUserSerializer.Meta.fields, 'avatar', 'is_subscribed')

    def get_is_subscribed(self, user_object: User) -> bool:
        """Проверяет подписку текущего пользователя."""
        current_user = self.context.get('request').user
        if not current_user.is_authenticated:
            return False
        return Subscription.objects.filter(
            author=user_object, subscriber=current_user
        ).exists()


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для управления аватаром пользователя."""

    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


# --------------------------------------------------------------------------- #
# Recipe-related serializers
# --------------------------------------------------------------------------- #
class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов рецепта с количеством."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source='ingredient'
    )
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit',
    )
    name = serializers.ReadOnlyField(source='ingredient.name')
    amount = serializers.IntegerField(
        validators=[
            MinValueValidator(
                limit_value=MIN_INGREDIENT_AMOUNT, message=MIN_AMOUNT_ERROR
            )
        ]
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """Универсальный сериализатор для модели Recipe."""

    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        source='recipeingredients', many=True, read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    # Поля для записи, которые будут использоваться в .create() и .update()
    image_b64 = Base64ImageField(
        source='image', write_only=True, required=True
    )
    tags_list = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all()),
        write_only=True,
    )
    ingredients_list = serializers.ListField(
        child=RecipeIngredientSerializer(), write_only=True
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
            # write-only fields
            'image_b64',
            'tags_list',
            'ingredients_list',
        )
        read_only_fields = (
            'id',
            'author',
            'tags',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'image',
        )

    def get_is_favorited(self, recipe: Recipe) -> bool:
        """Проверяет, находится ли рецепт в избранном."""
        user = self.context['request'].user
        return (
            user.is_authenticated
            and Favorite.objects.filter(user=user, recipe=recipe).exists()
        )

    def get_is_in_shopping_cart(self, recipe: Recipe) -> bool:
        """Проверяет, находится ли рецепт в списке покупок."""
        user = self.context['request'].user
        return (
            user.is_authenticated
            and ShoppingCart.objects.filter(user=user, recipe=recipe).exists()
        )

    def validate_tags_list(self, tags: List[Tag]) -> List[Tag]:
        """Проверяет теги на дубликаты и пустоту."""
        if not tags:
            raise serializers.ValidationError(
                'Нужно выбрать хотя бы один тег.'
            )
        if len(set(tag.id for tag in tags)) != len(tags):
            raise serializers.ValidationError('Теги не должны повторяться.')
        return tags

    def validate_ingredients_list(
        self, ingredients: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Проверяет ингредиенты на дубликаты и пустоту."""
        if not ingredients:
            raise serializers.ValidationError(
                'Нужно добавить хотя бы один ингредиент.'
            )
        ingredient_ids = [item['ingredient'].id for item in ingredients]
        if len(set(ingredient_ids)) != len(ingredient_ids):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться.'
            )
        return ingredients

    def create(self, validated_data: Dict[str, Any]) -> Recipe:
        """Создает рецепт через RecipeService."""
        author = self.context['request'].user
        # Переименовываем поля для совместимости с сервисом
        validated_data['tags'] = validated_data.pop('tags_list')
        validated_data['ingredients'] = validated_data.pop('ingredients_list')
        validated_data['image'] = validated_data.pop('image')

        return RecipeService.create_recipe(author, validated_data)

    def update(
        self, instance: Recipe, validated_data: Dict[str, Any]
    ) -> Recipe:
        """Обновляет рецепт через RecipeService."""
        # Переименовываем поля для совместимости с сервисом
        if 'tags_list' in validated_data:
            validated_data['tags'] = validated_data.pop('tags_list')
        if 'ingredients_list' in validated_data:
            validated_data['ingredients'] = validated_data.pop(
                'ingredients_list'
            )
        if 'image' in validated_data:
            validated_data['image'] = validated_data.pop('image')

        return RecipeService.update_recipe(instance, validated_data)


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Краткое представление рецепта."""

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )
        read_only_fields = fields


# --------------------------------------------------------------------------- #
# Subscription serializers
# --------------------------------------------------------------------------- #
class ReadSubscriptionSerializer(UserSerializer):
    """Сериализатор для подписок с рецептами автора."""

    recipes_count = serializers.ReadOnlyField(source='recipes.count')
    recipes = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = (*UserSerializer.Meta.fields, 'recipes', 'recipes_count')

    def get_recipes(self, author_user: User) -> List[Dict[str, Any]]:
        """Получает ограниченный список рецептов автора."""
        request_context = self.context.get('request')
        recipes_limit = request_context.GET.get('recipes_limit', 10**10)
        limit_value = int(recipes_limit)
        author_recipes = author_user.recipes.all()[:limit_value]
        return ShortRecipeSerializer(
            author_recipes,
            context=self.context,
            many=True,
        ).data
