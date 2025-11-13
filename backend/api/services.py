from __future__ import annotations

from typing import Any, Dict, List, Tuple, Type

from django.db import transaction
from django.db.models import Model
from django.http import FileResponse

from . import utils
from .models import (
    Recipe,
    RecipeIngredient,
    Subscription,
    User,
)


class RecipeService:
    @staticmethod
    def _bulk_create_ingredients(
        recipe_instance: Recipe, ingredients_data: List[Dict[str, Any]]
    ) -> None:
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

    @classmethod
    @transaction.atomic
    def create_recipe(
        cls, author: User, validated_data: Dict[str, Any]
    ) -> Recipe:
        """Создает новый рецепт с тегами и ингредиентами."""
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')

        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.tags.set(tags_data)
        cls._bulk_create_ingredients(recipe, ingredients_data)
        return recipe

    @classmethod
    @transaction.atomic
    def update_recipe(
        cls, recipe: Recipe, validated_data: Dict[str, Any]
    ) -> Recipe:
        """Обновляет существующий рецепт, его теги и ингредиенты."""
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
    def manage_recipe_relation(
        user: User, recipe: Recipe, relation_model: Type[Model]
    ) -> Tuple[Model | None, bool]:
        """Создает или удаляет связь 'user-recipe' (избранное, корзина)."""
        instance, created = relation_model.objects.get_or_create(
            user=user, recipe=recipe
        )
        return (None, False) if not created else (instance, True)

    @staticmethod
    def remove_recipe_relation(
        user: User, recipe: Recipe, relation_model: Type[Model]
    ) -> bool:
        """Удаляет связь 'user-recipe'."""
        deleted_count, _ = relation_model.objects.filter(
            user=user, recipe=recipe
        ).delete()
        return deleted_count > 0

    @staticmethod
    def generate_shopping_cart_file(user: User) -> FileResponse:
        """Генерирует и возвращает файл со списком покупок."""
        from django.db.models import Sum

        ingredients = (
            RecipeIngredient.objects.filter(
                recipe__shoppingcarts__user=user
            )
            .select_related('recipe', 'ingredient')
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(amount=Sum('amount'))
            .order_by('ingredient__name')
        )
        recipes = Recipe.objects.filter(
            shoppingcarts__user=user
        ).distinct()

        file_content = utils.make_shopping_cart_file(ingredients, recipes)
        return FileResponse(
            file_content,
            as_attachment=True,
            filename='shopping_cart.txt',
            content_type='text/plain',
        )


class UserService:
    @staticmethod
    def subscribe_to_author(
        subscriber: User, author: User
    ) -> Tuple[Subscription | None, bool]:
        """Подписывает пользователя на автора."""
        if subscriber == author:
            return None, False

        subscription, created = Subscription.objects.get_or_create(
            subscriber=subscriber, author=author
        )
        return (subscription, True) if created else (None, False)

    @staticmethod
    def unsubscribe_from_author(subscriber: User, author: User) -> bool:
        """Отписывает пользователя от автора."""
        deleted_count, _ = Subscription.objects.filter(
            subscriber=subscriber, author=author
        ).delete()
        return deleted_count > 0

    @staticmethod
    def get_user_subscriptions(user: User):
        """Возвращает QuerySet авторов, на которых подписан пользователь."""
        return User.objects.filter(authors__subscriber=user)
