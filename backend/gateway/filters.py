"""Filter classes for API query parameter filtering."""
from django.db.models import QuerySet
from django_filters.rest_framework import FilterSet
from django_filters.rest_framework.filters import (
    BooleanFilter,
    ModelMultipleChoiceFilter,
)
from rest_framework.filters import SearchFilter

from cookbook.models import Category, CulinaryItem


class ComponentSearchFilter(SearchFilter):
    """
    Search filter for component/ingredient lookup.

    Provides case-insensitive prefix matching for component names.
    """
    search_param = 'name'


class CulinaryItemFilterSet(FilterSet):
    """
    Filter set for culinary item queries.

    Supports filtering by categories, author, bookmark status,
    and wishlist status.
    """
    categories = ModelMultipleChoiceFilter(
        field_name='categories__slug',
        to_field_name='slug',
        queryset=Category.objects.all(),
        label='Filter by category slugs',
    )
    is_bookmarked = BooleanFilter(
        method='filter_bookmarked',
        label='Show only bookmarked items',
    )
    is_in_wishlist = BooleanFilter(
        method='filter_wishlist',
        label='Show only items in wishlist',
    )

    class Meta:
        model = CulinaryItem
        fields = ('categories', 'author', 'is_bookmarked', 'is_in_wishlist')

    def filter_bookmarked(
        self, queryset: QuerySet, name: str, value: bool
    ) -> QuerySet:
        """
        Filter items by bookmark status for the current user.

        Args:
            queryset: Base queryset to filter.
            name: Filter field name (unused).
            value: Boolean indicating if bookmarked items should be shown.

        Returns:
            Filtered queryset.
        """
        if not value:
            return queryset

        user = self.request.user
        if not user.is_authenticated:
            return queryset.none()

        from cookbook.models import Bookmark
        return queryset.filter(
            id__in=Bookmark.objects.filter(account=user).values_list('item_id')
        )

    def filter_wishlist(
        self, queryset: QuerySet, name: str, value: bool
    ) -> QuerySet:
        """
        Filter items by wishlist status for the current user.

        Args:
            queryset: Base queryset to filter.
            name: Filter field name (unused).
            value: Boolean indicating if wishlist items should be shown.

        Returns:
            Filtered queryset.
        """
        if not value:
            return queryset

        user = self.request.user
        if not user.is_authenticated:
            return queryset.none()

        from cookbook.models import WishlistItem
        return queryset.filter(
            id__in=WishlistItem.objects.filter(
                account=user
            ).values_list('item_id')
        )
