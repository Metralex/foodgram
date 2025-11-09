from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import transaction
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

User = get_user_model()

DUPLICATE_ERROR_MSG = 'Обнаружены дублирующиеся элементы: {}'
EMPTY_IMAGE_ERROR = 'Изображение не может отсутствовать'
MIN_AMOUNT = 1
MIN_AMOUNT_ERROR = f'Количество должно быть не менее {MIN_AMOUNT}'


class TagSerializer(serializers.ModelSerializer):
    """Сериализация данных тега."""

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализация данных ингредиента."""

    class Meta:
        model = Ingredient
        fields = '__all__'


class UserSerializer(DjoserUserSerializer):
    """Расширенный сериализатор пользователя с проверкой подписки."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (*DjoserUserSerializer.Meta.fields, 'avatar', 'is_subscribed')

    def get_is_subscribed(self, user_object):
        current_user = self.context.get('request').user
        if not current_user.is_authenticated:
            return False
        return Subscription.objects.filter(
            author=user_object, subscriber=current_user
        ).exists()


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с аватаром пользователя."""

    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализация ингредиента рецепта с количеством."""

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
                limit_value=MIN_AMOUNT, message=MIN_AMOUNT_ERROR
            )
        ]
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class ReadRecipeSerializer(serializers.ModelSerializer):
    """Сериализация полной информации о рецепте для чтения."""

    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    ingredients = RecipeIngredientSerializer(
        source='recipeingredients', many=True
    )
    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True)

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

    def _check_user_relation(self, recipe_obj, relation_model):
        """Проверяет наличие связи пользователя с рецептом."""
        current_user = self.context.get('request').user
        if not current_user.is_authenticated:
            return False
        return relation_model.objects.filter(
            user=current_user, recipe=recipe_obj
        ).exists()

    def get_is_favorited(self, recipe_obj):
        return self._check_user_relation(recipe_obj, Favorite)

    def get_is_in_shopping_cart(self, recipe_obj):
        return self._check_user_relation(recipe_obj, ShoppingCart)


class WriteRecipeSerializer(serializers.ModelSerializer):
    """Сериализация создания и редактирования рецепта."""

    image = Base64ImageField(allow_empty_file=False, required=True)
    tags = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(
            queryset=Tag.objects.all(),
        ),
        allow_empty=False,
        required=True,
    )
    ingredients = serializers.ListField(
        child=RecipeIngredientSerializer(),
        allow_empty=False,
        required=True,
    )

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

    def _validate_no_duplicates(self, items_list, field_identifier):
        """Проверяет отсутствие дубликатов в списке."""
        seen = set()
        duplicates = set()
        for item in items_list:
            if item in seen:
                duplicates.add(item)
            seen.add(item)
        if duplicates:
            raise serializers.ValidationError(
                {field_identifier: DUPLICATE_ERROR_MSG.format(duplicates)}
            )

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError(EMPTY_IMAGE_ERROR)
        return value

    def validate_tags(self, value):
        tag_ids = [tag.id for tag in value]
        self._validate_no_duplicates(tag_ids, 'tags')
        return value

    def validate_ingredients(self, value):
        ingredient_ids = [item['ingredient'].id for item in value]
        self._validate_no_duplicates(ingredient_ids, 'ingredients')
        return value

    def _bulk_create_ingredients(self, recipe_instance, ingredients_data):
        """Массово создает связи ингредиентов с рецептом."""
        ingredient_relations = [
            RecipeIngredient(
                recipe=recipe_instance,
                ingredient=item['ingredient'],
                amount=item['amount'],
            )
            for item in ingredients_data
        ]
        RecipeIngredient.objects.bulk_create(ingredient_relations)

    @transaction.atomic
    def create(self, validated_data):
        ingredients_payload = validated_data.pop('ingredients')
        recipe_instance = super().create(validated_data)
        self._bulk_create_ingredients(recipe_instance, ingredients_payload)
        return recipe_instance

    @transaction.atomic
    def update(self, instance, validated_data):
        if 'ingredients' in validated_data:
            ingredients_payload = validated_data.pop('ingredients')
            instance.ingredients.clear()
            self._bulk_create_ingredients(instance, ingredients_payload)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return ReadRecipeSerializer(instance, context=self.context).data


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Упрощенное представление рецепта."""

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )


class ReadSubscriptionSerializer(UserSerializer):
    """Сериализация данных подписки с рецептами автора."""

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
            author_recipes,
            context=self.context,
            many=True,
        ).data
