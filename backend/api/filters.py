from django.db.models import QuerySet
from django_filters import rest_framework as df_filters
from rest_framework import filters as drf_filters

from .models import Recipe, Tag


class IngredientFilter(drf_filters.SearchFilter):
    """Provide prefix search queries for ingredient names."""

    search_param = "name"

    def get_search_terms(self, request):
        terms = super().get_search_terms(request)
        return [term.strip() for term in terms if term.strip()]


class RecipeFilterSet(df_filters.FilterSet):
    """Filter recipes by tags, author and user-specific flags."""

    tags = df_filters.ModelMultipleChoiceFilter(
        field_name="tags__slug",
        to_field_name="slug",
        queryset=Tag.objects.all(),
    )
    is_favorited = df_filters.BooleanFilter(method="filter_by_favorites")
    is_in_shopping_cart = df_filters.BooleanFilter(
        method="filter_by_shopping_cart"
    )

    class Meta:
        model = Recipe
        fields = ("tags", "author", "is_favorited", "is_in_shopping_cart")

    def _filter_by_relation(
        self, queryset: QuerySet, value: bool, relation: str
    ) -> QuerySet:
        if not value or not self.request.user.is_authenticated:
            return queryset
        lookup = f"{relation}__user"
        return queryset.filter(**{lookup: self.request.user})

    def filter_by_favorites(
        self, queryset: QuerySet, _name: str, value: bool
    ) -> QuerySet:
        return self._filter_by_relation(queryset, value, "favorites")

    def filter_by_shopping_cart(
        self, queryset: QuerySet, _name: str, value: bool
    ) -> QuerySet:
        return self._filter_by_relation(queryset, value, "shoppingcarts")
