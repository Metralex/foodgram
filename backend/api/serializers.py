from __future__ import annotations

from collections import Counter
from typing import Iterable, Sequence

from django.contrib.auth import get_user_model
from django.db import transaction
from djoser.serializers import UserSerializer as BaseUserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from .models import Ingredient, Recipe, RecipeIngredient, Subscription, Tag

User = get_user_model()


def _collect_duplicates(values: Iterable) -> set:
    counts = Counter(values)
    return {value for value, quantity in counts.items() if quantity > 1}


class UserSerializer(BaseUserSerializer):
    """Extend Djoser serializer with subscription status and avatar field."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta(BaseUserSerializer.Meta):
        model = User
        fields = (*BaseUserSerializer.Meta.fields, "avatar", "is_subscribed")

    def get_is_subscribed(self, author):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return Subscription.objects.filter(
            author=author, subscriber=request.user
        ).exists()


class AvatarSerializer(serializers.ModelSerializer):
    """Serializer used for updating user avatars."""

    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ("avatar",)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = "__all__"


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = "__all__"


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source="ingredient"
    )
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(
        source="ingredient.measurement_unit"
    )

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")


class IngredientAmountSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=1)


class ReadRecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientReadSerializer(
        source="recipeingredients", many=True
    )
    is_in_shopping_cart = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "name",
            "image",
            "text",
            "cooking_time",
            "is_in_shopping_cart",
            "is_favorited",
        )
        read_only_fields = fields

    def _user(self):
        request = self.context.get("request")
        return getattr(request, "user", None)

    def get_is_in_shopping_cart(self, recipe):
        user = self._user()
        return bool(
            user
            and user.is_authenticated
            and recipe.shoppingcarts.filter(user=user).exists()
        )

    def get_is_favorited(self, recipe):
        user = self._user()
        return bool(
            user
            and user.is_authenticated
            and recipe.favorites.filter(user=user).exists()
        )


class WriteRecipeSerializer(serializers.ModelSerializer):
    ingredients = IngredientAmountSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all()
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            "ingredients",
            "tags",
            "image",
            "name",
            "text",
            "cooking_time",
        )

    def _validate_duplicates(self, values: Sequence, field_name: str):
        duplicates = _collect_duplicates(values)
        if duplicates:
            raise serializers.ValidationError(
                {field_name: f"Дубликаты не допускаются: {sorted(duplicates)}"}
            )

    def validate_tags(self, tags):
        self._validate_duplicates([tag.id for tag in tags], "tags")
        return tags

    def validate_ingredients(self, ingredients):
        self._validate_duplicates(
            [item["id"].id for item in ingredients], "ingredients"
        )
        return ingredients

    def _save_ingredients(self, recipe: Recipe, ingredients_data):
        RecipeIngredient.objects.filter(recipe=recipe).delete()
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient=item["id"],
                amount=item["amount"],
            )
            for item in ingredients_data
        )

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop("ingredients")
        recipe = super().create(validated_data)
        self._save_ingredients(recipe, ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients = validated_data.pop("ingredients", None)
        recipe = super().update(instance, validated_data)
        if ingredients is not None:
            self._save_ingredients(recipe, ingredients)
        return recipe

    def to_representation(self, instance):
        return ReadRecipeSerializer(instance, context=self.context).data


class ShortRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class ReadSubscriptionSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(source="recipes.count")

    class Meta(UserSerializer.Meta):
        fields = (*UserSerializer.Meta.fields, "recipes", "recipes_count")

    def _resolve_limit(self):
        request = self.context.get("request")
        if not request:
            return None
        value = request.GET.get("recipes_limit")
        if not value:
            return None
        try:
            return max(int(value), 0)
        except (TypeError, ValueError):
            return None

    def get_recipes(self, user):
        limit = self._resolve_limit()
        queryset = user.recipes.all()
        if limit is not None:
            queryset = queryset[:limit]
        serializer = ShortRecipeSerializer(
            queryset, many=True, context=self.context
        )
        return serializer.data
