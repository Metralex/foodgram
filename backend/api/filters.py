"""Фильтры для API Foodgram."""

from __future__ import annotations

from django.db.models import QuerySet
from django_filters.rest_framework import FilterSet
from django_filters.rest_framework.filters import (
    BooleanFilter,
    ModelMultipleChoiceFilter,
)
from rest_framework.filters import SearchFilter

from .models import Recipe, Tag


class IngredientFilter(SearchFilter):
    """Фильтр поиска ингредиентов по имени."""

    search_param = "name"


class RecipeFilterSet(FilterSet):
    """Набор фильтров для рецептов."""

    is_in_shopping_cart = BooleanFilter(method="filter_shopping_cart")
    is_favorited = BooleanFilter(method="filter_favorites")
    tags = ModelMultipleChoiceFilter(
        field_name="tags__slug",
        to_field_name="slug",
        queryset=Tag.objects.all(),
    )

    class Meta:
        model = Recipe
        fields = ("tags", "author", "is_favorited", "is_in_shopping_cart")

    def filter_favorites(
        self, queryset: QuerySet[Recipe], field_name: str, flag_value: bool
    ) -> QuerySet[Recipe]:
        """Фильтрует рецепты по наличию в избранном."""
        current_user = self.request.user
        if current_user.is_authenticated and flag_value:
            return queryset.filter(favorites__user=current_user)
        return queryset

    def filter_shopping_cart(
        self, queryset: QuerySet[Recipe], field_name: str, flag_value: bool
    ) -> QuerySet[Recipe]:
        """Фильтрует рецепты по наличию в списке покупок."""
        current_user = self.request.user
        if current_user.is_authenticated and flag_value:
            return queryset.filter(shoppingcarts__user=current_user)
        return queryset
