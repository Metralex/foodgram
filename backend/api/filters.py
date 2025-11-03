"""
API filters for foodgram application.

This module contains filter classes for filtering querysets
based on query parameters.
"""
from django.db.models import QuerySet
from django_filters.rest_framework import FilterSet
from django_filters.rest_framework.filters import (
    BooleanFilter,
    ModelMultipleChoiceFilter,
)
from rest_framework.filters import SearchFilter

from recipes.models import Recipe, Tag


class IngredientFilter(SearchFilter):
    """
    Filter for ingredient search by name.

    Uses case-insensitive search with prefix matching.
    """
    search_param = 'name'


class RecipeFilterSet(FilterSet):
    """
    FilterSet for recipe filtering.

    Supports filtering by tags, author, favorites, and shopping cart.
    """
    tags = ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
        label='Tags (filter by slug)',
    )
    is_favorited = BooleanFilter(
        method='filter_favorited',
        label='Show only favorited recipes',
    )
    is_in_shopping_cart = BooleanFilter(
        method='filter_shopping_cart',
        label='Show only recipes in shopping cart',
    )

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_favorited', 'is_in_shopping_cart')

    def filter_favorited(
        self, queryset: QuerySet, name: str, value: bool
    ) -> QuerySet:
        """
        Filter recipes by favorite status for current user.

        Args:
            queryset: Base recipe queryset.
            name: Filter field name (unused).
            value: Boolean value indicating if favorites should be shown.

        Returns:
            Filtered queryset.
        """
        if not value:
            return queryset

        user = self.request.user
        if not user.is_authenticated:
            return queryset.none()

        return queryset.filter(favorites__user=user)

    def filter_shopping_cart(
        self, queryset: QuerySet, name: str, value: bool
    ) -> QuerySet:
        """
        Filter recipes by shopping cart status for current user.

        Args:
            queryset: Base recipe queryset.
            name: Filter field name (unused).
            value: Boolean indicating if shopping cart items should be shown.

        Returns:
            Filtered queryset.
        """
        if not value:
            return queryset

        user = self.request.user
        if not user.is_authenticated:
            return queryset.none()

        return queryset.filter(shoppingcarts__user=user)
