"""Сериализаторы для API Foodgram."""

from djoser.serializers import UserSerializer as DjoserUserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator

from recipes.models import Favorite, Ingredient, Recipe, RecipeIngredient, ShoppingCart, Tag
from users.models import Subscription


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
        """Проверяет, подписан ли текущий пользователь на автора."""
        current_user = self.context.get('request').user
        if not current_user.is_authenticated:
            return False
        return Subscription.objects.filter(
            author=user_object, subscriber=current_user
        ).exists()


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

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        source='recipeingredients', many=True
    )
    image = Base64ImageField(required=False, allow_null=True)
    is_favorited = serializers.BooleanField(read_only=True, default=False)
    is_in_shopping_cart = serializers.BooleanField(
        read_only=True, default=False
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
        )
        read_only_fields = (
            'id',
            'author',
            'is_favorited',
            'is_in_shopping_cart',
        )

    def validate_tags(self, tags):
        """Валидация списка тегов."""
        if not tags:
            message = 'Нужно выбрать хотя бы один тег.'
            raise serializers.ValidationError(message)
        if len(set(tag.id for tag in tags)) != len(tags):
            message = 'Теги не должны повторяться.'
            raise serializers.ValidationError(message)
        return tags

    def validate_ingredients(self, ingredients):
        """Валидация списка ингредиентов."""
        if not ingredients or not isinstance(ingredients, list):
            message = 'Нужно добавить хотя бы один ингредиент.'
            raise serializers.ValidationError(message)
        ingredient_ids = []
        for item in ingredients:
            ingredient_instance = item.get('ingredient')
            if ingredient_instance is None:
                message = 'Ингредиент должен быть указан.'
                raise serializers.ValidationError(message)
            ingredient_ids.append(ingredient_instance.id)
        if not ingredient_ids:
            message = 'Нужно добавить хотя бы один ингредиент.'
            raise serializers.ValidationError(message)
        if len(set(ingredient_ids)) != len(ingredient_ids):
            message = 'Ингредиенты не должны повторяться.'
            raise serializers.ValidationError(message)
        return ingredients

    def _set_tags(self, recipe, tags_data):
        """Устанавливает теги рецепта."""
        recipe.tags.set(tags_data)

    def _set_ingredients(self, recipe, ingredients_data):
        """Создает связи рецепта с ингредиентами."""
        if not ingredients_data:
            return

        RecipeIngredient.objects.bulk_create(
            [
                RecipeIngredient(
                    recipe=recipe,
                    ingredient=item['ingredient'],
                    amount=item['amount'],
                )
                for item in ingredients_data
            ]
        )

    def create(self, validated_data):
        """Создает новый рецепт."""
        author = self.context['request'].user
        ingredients_data = validated_data.pop('recipeingredients', [])
        tags_data = validated_data.pop('tags', [])

        recipe = Recipe.objects.create(author=author, **validated_data)
        self._set_tags(recipe, tags_data)
        self._set_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        """Обновляет рецепт."""
        tags_data = validated_data.pop('tags', None)
        ingredients_data = validated_data.pop('recipeingredients', None)

        if tags_data is not None:
            self._set_tags(instance, tags_data)

        if ingredients_data is not None:
            instance.ingredients.clear()
            self._set_ingredients(instance, ingredients_data)

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """Возвращает представление рецепта с подробной информацией."""
        representation = super().to_representation(instance)
        representation['tags'] = TagSerializer(
            instance.tags.all(), many=True, context=self.context
        ).data
        representation['ingredients'] = RecipeIngredientSerializer(
            instance.recipeingredients.all(),
            many=True,
            context=self.context,
        ).data
        return representation


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
        """Возвращает список рецептов с учетом лимита."""
        request_context = self.context.get('request')
        recipes_limit = request_context.GET.get('recipes_limit', 10**10)
        limit_value = int(recipes_limit)
        author_recipes = author_user.recipes.all()[:limit_value]
        return ShortRecipeSerializer(
            author_recipes, context=self.context, many=True
        ).data


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для избранного."""

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')

    def validate(self, data):
        """Проверка на дублирование."""
        if Favorite.objects.filter(
            user=data['user'], recipe=data['recipe']
        ).exists():
            raise serializers.ValidationError('Рецепт уже есть в избранном')
        return data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для списка покупок."""

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')

    def validate(self, data):
        """Проверка на дублирование."""
        if ShoppingCart.objects.filter(
            user=data['user'], recipe=data['recipe']
        ).exists():
            raise serializers.ValidationError(
                'Рецепт уже есть в списке покупок'
            )
        return data


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для подписок."""

    class Meta:
        model = Subscription
        fields = ('subscriber', 'author')

    def validate(self, data):
        """Проверка на корректность подписки."""
        if data['subscriber'] == data['author']:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя'
            )
        if Subscription.objects.filter(
            subscriber=data['subscriber'], author=data['author']
        ).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого автора'
            )
        return data
