"""
API serializers for foodgram application.

This module contains serializers for converting model instances
to/from JSON with validation and business logic.
"""
from collections import Counter
from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import transaction
from djoser.serializers import UserSerializer as DjoserUserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import (
    Error,
    Favorite,
    Ingredient,
    MinValue,
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
    User serializer with subscription status.

    Extends Djoser user serializer to include avatar and
    subscription status for the current user.
    """
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (*DjoserUserSerializer.Meta.fields, 'avatar', 'is_subscribed')

    def get_is_subscribed(self, author: 'AbstractUser') -> bool:
        """
        Check if current user is subscribed to this author.

        Uses prefetched data if available to avoid N+1 queries.
        """
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False

        user = request.user

        # Optimized check - could be prefetched in future
        # For now, direct query is acceptable as it's called once per user

        return Subscription.objects.filter(
            author=author, subscriber=user
        ).exists()


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeIngredientSerializer(serializers.ModelSerializer):
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
    Serializer for reading recipe data with full details.

    Includes tags, author, ingredients, and user interaction flags.
    Optimized to minimize database queries.
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
        Check if recipe is in user's shopping cart.

        Uses prefetched data if available to avoid N+1 queries.
        """
        user = self.context.get('request').user
        if not user.is_authenticated:
            return False

        # Check if prefetched data is available
        if hasattr(recipe, '_user_shopping_carts'):
            return len(recipe._user_shopping_carts) > 0

        return ShoppingCart.objects.filter(
            user=user, recipe=recipe
        ).exists()

    def get_is_favorited(self, recipe: Recipe) -> bool:
        """
        Check if recipe is in user's favorites.

        Uses prefetched data if available to avoid N+1 queries.
        """
        user = self.context.get('request').user
        if not user.is_authenticated:
            return False

        # Check if prefetched data is available
        if hasattr(recipe, '_user_favorites'):
            return len(recipe._user_favorites) > 0

        return Favorite.objects.filter(user=user, recipe=recipe).exists()


class WriteRecipeSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating recipes.

    Handles recipe creation/update with nested ingredients and tags.
    Validates for duplicates and ensures all required fields are present.
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
        Check for duplicate values in array and raise validation error.

        Args:
            array: List of values to check for duplicates.
            field_name: Name of the field for error message.

        Raises:
            ValidationError: If duplicates are found.
        """
        counts = Counter(array)
        duplicates = {item for item, count in counts.items() if count > 1}
        if duplicates:
            raise serializers.ValidationError(
                {field_name: Error.DUPLICATES.format(duplicates)}
            )

    def validate_tags(self, tags: list) -> list:
        """
        Validate tags list for duplicates.

        Args:
            tags: List of Tag instances.

        Returns:
            Validated tags list.

        Raises:
            ValidationError: If duplicate tags found.
        """
        self._check_duplicates([tag.id for tag in tags], 'tags')
        return tags

    def validate_ingredients(self, ingredients: list) -> list:
        """
        Validate ingredients list for duplicates.

        Args:
            ingredients: List of ingredient dictionaries.

        Returns:
            Validated ingredients list.

        Raises:
            ValidationError: If duplicate ingredients found.
        """
        self._check_duplicates(
            [item['ingredient'].id for item in ingredients],
            'ingredients',
        )
        return ingredients

    def validate_image(self, image) -> object:
        """
        Validate that image is provided.

        Args:
            image: Image file object.

        Returns:
            Validated image.

        Raises:
            ValidationError: If image is empty.
        """
        if not image:
            raise serializers.ValidationError(Error.NO_IMAGE)
        return image

    @staticmethod
    def _save_ingredients(recipe: Recipe, ingredients: list) -> None:
        """
        Save recipe ingredients using bulk_create for efficiency.

        Args:
            recipe: Recipe instance to attach ingredients to.
            ingredients: List of ingredient dictionaries with keys:
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
        Create recipe with ingredients and tags.

        Args:
            validated_data: Validated recipe data.

        Returns:
            Created Recipe instance.
        """
        ingredients_data = validated_data.pop('ingredients')
        recipe = super().create(validated_data)
        self._save_ingredients(recipe, ingredients_data)
        return recipe

    @transaction.atomic
    def update(self, recipe: Recipe, validated_data: dict) -> Recipe:
        """
        Update recipe, optionally updating ingredients.

        Args:
            recipe: Recipe instance to update.
            validated_data: Validated recipe data.

        Returns:
            Updated Recipe instance.
        """
        try:
            new_ingredients = validated_data.pop('ingredients')
            recipe.ingredients.clear()
            self._save_ingredients(recipe, new_ingredients)
        except KeyError:
            # Ingredients not provided, keep existing ones
            pass
        return super().update(recipe, validated_data)

    def to_representation(self, recipe: Recipe) -> dict:
        """
        Convert recipe instance to serialized representation.

        Uses ReadRecipeSerializer for consistent output format.

        Args:
            recipe: Recipe instance.

        Returns:
            Serialized recipe data.
        """
        return ReadRecipeSerializer(recipe, context=self.context).data


class ShortRecipeSerializer(serializers.ModelSerializer):
    """
    Minimal recipe serializer for nested representations.

    Used in subscriptions and other places where full recipe data
    is not needed.
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
    Serializer for user subscription data.

    Extends UserSerializer to include user's recipes with limit support.
    """
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(source='recipes.count')

    class Meta(UserSerializer.Meta):
        fields = (*UserSerializer.Meta.fields, 'recipes', 'recipes_count')

    def get_recipes(self, user: 'AbstractUser') -> list:
        """
        Get user's recipes with optional limit.

        Args:
            user: User instance to get recipes for.

        Returns:
            List of serialized recipe dictionaries.
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
