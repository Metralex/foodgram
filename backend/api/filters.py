"""
Фильтры для API приложения Foodgram.

Модуль содержит классы фильтров для фильтрации querysets
на основе параметров запроса.
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
    Фильтр для поиска ингредиентов по названию.

    Использует поиск без учёта регистра с совпадением префикса.
    """
    search_param = 'name'


class RecipeFilterSet(FilterSet):
    """
    Набор фильтров для фильтрации блюд.

    Поддерживает фильтрацию по категориям, автору, избранному и
    списку покупок.
    """
    tags = ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
        label='Категории (фильтр по slug)',
    )
    is_favorited = BooleanFilter(
        method='filter_favorited',
        label='Показать только избранные блюда',
    )
    is_in_shopping_cart = BooleanFilter(
        method='filter_shopping_cart',
        label='Показать только блюда в списке покупок',
    )

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_favorited', 'is_in_shopping_cart')

    def filter_favorited(
        self, queryset: QuerySet, name: str, value: bool
    ) -> QuerySet:
        """
        Фильтровать блюда по статусу избранного текущего пользователя.

        Аргументы:
            queryset: Базовый queryset блюд.
            name: Имя поля фильтра (не используется).
            value: Логическое значение, указывающее, должны ли быть
                   показаны избранные.

        Возвращает:
            Отфильтрованный queryset.
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
        Фильтровать блюда по статусу в списке покупок текущего
        пользователя.

        Аргументы:
            queryset: Базовый queryset блюд.
            name: Имя поля фильтра (не используется).
            value: Логическое значение, указывающее, должны ли быть
                   показаны в корзине.

        Возвращает:
            Отфильтрованный queryset.
        """
        if not value:
            return queryset

        user = self.request.user
        if not user.is_authenticated:
            return queryset.none()

        return queryset.filter(shoppingcarts__user=user)
