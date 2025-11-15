from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from djoser.serializers import UserSerializer as DjoserUserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Subscription, Tag)

User = get_user_model()


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')
        read_only_fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')
        read_only_fields = ('id', 'name', 'measurement_unit')


class UserSerializer(DjoserUserSerializer):
    """Сериализатор для пользователей."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (*DjoserUserSerializer.Meta.fields, 'avatar', 'is_subscribed')

    def get_is_subscribed(self, user_object):
        current_user = self.context.get('request').user
        if not current_user.is_authenticated:
            return False
        return (
            Subscription.objects.filter(
                author=user_object, subscriber=current_user
            ).exists()
        )


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для аватаров."""

    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов в рецепте."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source='ingredient'
    )
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )
    name = serializers.ReadOnlyField(source='ingredient.name')
    amount = serializers.IntegerField(
        validators=[MinValueValidator(1, 'Минимум 1')]
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов."""

    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        source='recipeingredients', many=True, read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    image_b64 = Base64ImageField(
        source='image', write_only=True, required=True
    )
    tags_list = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(
            queryset=Tag.objects.all()
        ),
        write_only=True,
    )
    ingredients_list = serializers.ListField(
        child=RecipeIngredientSerializer(), write_only=True
    )

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time',
            'image_b64', 'tags_list', 'ingredients_list',
        )
        read_only_fields = (
            'id', 'author', 'tags', 'ingredients',
            'is_favorited', 'is_in_shopping_cart', 'image',
        )

    def get_is_favorited(self, recipe):
        user = self.context['request'].user
        return (
            user.is_authenticated
            and Favorite.objects.filter(user=user, recipe=recipe).exists()
        )

    def get_is_in_shopping_cart(self, recipe):
        user = self.context['request'].user
        return (
            user.is_authenticated
            and ShoppingCart.objects.filter(user=user, recipe=recipe).exists()
        )

    def validate_tags_list(self, tags):
        if not tags:
            message = 'Нужно выбрать хотя бы один тег.'
            raise serializers.ValidationError(message)
        if len(set(tag.id for tag in tags)) != len(tags):
            message = 'Теги не должны повторяться.'
            raise serializers.ValidationError(message)
        return tags

    def validate_ingredients_list(self, ingredients):
        if not ingredients:
            message = 'Нужно добавить хотя бы один ингредиент.'
            raise serializers.ValidationError(message)
        ingredient_ids = [item['ingredient'].id for item in ingredients]
        if len(set(ingredient_ids)) != len(ingredient_ids):
            message = 'Ингредиенты не должны повторяться.'
            raise serializers.ValidationError(message)
        return ingredients

    def create(self, validated_data):
        """Создает новый рецепт."""
        author = self.context['request'].user
        ingredients_data = validated_data.pop('ingredients_list')
        tags_data = validated_data.pop('tags_list')
        image = validated_data.pop('image')

        recipe = Recipe.objects.create(
            author=author, image=image, **validated_data
        )
        recipe.tags.set(tags_data)

        # Создаем связи с ингредиентами
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient=item['ingredient'],
                amount=item['amount'],
            )
            for item in ingredients_data
        ])
        return recipe

    def update(self, instance, validated_data):
        """Обновляет рецепт."""
        if 'tags_list' in validated_data:
            instance.tags.set(validated_data.pop('tags_list'))

        if 'ingredients_list' in validated_data:
            ingredients_data = validated_data.pop('ingredients_list')
            instance.ingredients.clear()
            RecipeIngredient.objects.bulk_create([
                RecipeIngredient(
                    recipe=instance,
                    ingredient=item['ingredient'],
                    amount=item['amount'],
                )
                for item in ingredients_data
            ])

        if 'image' in validated_data:
            instance.image = validated_data.pop('image')

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для краткого представления рецептов."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = fields


class ReadSubscriptionSerializer(UserSerializer):
    """Сериализатор для подписок."""

    recipes_count = serializers.ReadOnlyField(source='recipes.count')
    recipes = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = (*UserSerializer.Meta.fields, 'recipes', 'recipes_count')

    def get_recipes(self, author_user):
        request_context = self.context.get('request')
        recipes_limit = request_context.GET.get('recipes_limit', 10**10)
        limit_value = int(recipes_limit)
        author_recipes = author_user.recipes.all()[:limit_value]
        return ShortRecipeSerializer(
            author_recipes, context=self.context, many=True
        ).data
