from typing import Any, Dict, List, Tuple, Type

from django.db import transaction
from django.db.models import Model, Sum
from django.http import FileResponse

from . import utils
from .models import Recipe, RecipeIngredient, Subscription, User


class RecipeService:
    """Сервис для работы с рецептами."""

    @staticmethod
    def _bulk_create_ingredients(recipe, ingredients_data):
        """Создает ингредиенты для рецепта."""
        ingredient_relations = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=item['ingredient'],
                amount=item['amount'],
            )
            for item in ingredients_data
        ]
        RecipeIngredient.objects.bulk_create(ingredient_relations)

    @classmethod
    @transaction.atomic
    def create_recipe(cls, author, validated_data):
        """Создает новый рецепт."""
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')

        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.tags.set(tags_data)
        cls._bulk_create_ingredients(recipe, ingredients_data)
        return recipe

    @classmethod
    @transaction.atomic
    def update_recipe(cls, recipe, validated_data):
        """Обновляет рецепт."""
        if 'tags' in validated_data:
            recipe.tags.set(validated_data.pop('tags'))

        if 'ingredients' in validated_data:
            ingredients_data = validated_data.pop('ingredients')
            recipe.ingredients.clear()
            cls._bulk_create_ingredients(recipe, ingredients_data)

        for attr, value in validated_data.items():
            setattr(recipe, attr, value)

        recipe.save()
        return recipe

    @staticmethod
    def manage_recipe_relation(user, recipe, relation_model):
        """Добавляет рецепт в избранное или список покупок."""
        instance, created = relation_model.objects.get_or_create(user=user, recipe=recipe)
        return (None, False) if not created else (instance, True)

    @staticmethod
    def remove_recipe_relation(user, recipe, relation_model):
        """Удаляет рецепт из избранного или списка покупок."""
        deleted_count, _ = relation_model.objects.filter(user=user, recipe=recipe).delete()
        return deleted_count > 0

    @staticmethod
    def generate_shopping_cart_file(user):
        """Генерирует файл со списком покупок."""
        from django.db.models import Sum

        ingredients = (
            RecipeIngredient.objects.filter(recipe__shoppingcarts__user=user)
            .select_related('recipe', 'ingredient')
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(amount=Sum('amount'))
            .order_by('ingredient__name')
        )
        recipes = Recipe.objects.filter(shoppingcarts__user=user).distinct()

        file_content = utils.make_shopping_cart_file(ingredients, recipes)
        return FileResponse(
            file_content,
            as_attachment=True,
            filename='shopping_cart.txt',
            content_type='text/plain',
        )


class UserService:
    """Сервис для работы с пользователями."""

    @staticmethod
    def subscribe_to_author(subscriber, author):
        """Подписывает пользователя на автора."""
        if subscriber == author:
            return None, False

        subscription, created = Subscription.objects.get_or_create(
            subscriber=subscriber, author=author
        )
        return (subscription, True) if created else (None, False)

    @staticmethod
    def unsubscribe_from_author(subscriber, author):
        """Отписывает пользователя от автора."""
        deleted_count, _ = Subscription.objects.filter(
            subscriber=subscriber, author=author
        ).delete()
        return deleted_count > 0

    @staticmethod
    def get_user_subscriptions(user):
        """Возвращает авторов, на которых подписан пользователь."""
        return User.objects.filter(authors__subscriber=user)
