"""Конфигурация Django admin для рецептов."""

from django.contrib import admin
from django.db.models import Count

from .models import (
    Favorite, Ingredient, Recipe, RecipeIngredient, ShoppingCart, Tag,
)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Админка для управления тегами рецептов."""

    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    list_display = ('slug', 'name')
    ordering = ('name',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Админка для управления ингредиентами."""

    list_filter = ('measurement_unit',)
    search_fields = ('name',)
    list_display = ('name', 'measurement_unit')
    ordering = ('name',)


class RecipeIngredientInline(admin.TabularInline):
    """Inline редактор для ингредиентов рецепта."""

    extra = 1
    model = RecipeIngredient
    autocomplete_fields = ('ingredient',)
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Админка для управления рецептами."""

    filter_horizontal = ('tags',)
    inlines = [RecipeIngredientInline]
    list_filter = ('tags', 'author')
    search_fields = ('author__username', 'name')
    list_display = (
        'name',
        'author',
        'pub_date',
        'cooking_time',
        'get_favorites_count',
    )
    readonly_fields = ('short_url_code', 'get_favorites_count')
    ordering = ('-pub_date',)
    list_select_related = ('author',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return (
            queryset.select_related('author')
            .prefetch_related(
                'tags',
                'ingredients',
                'recipeingredient_set__ingredient',
            )
            .annotate(favorites_count=Count('favorites', distinct=True))
        )

    def get_favorites_count(self, obj: Recipe) -> int:
        return obj.favorites_count


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Админка для управления избранными рецептами."""

    search_fields = ('recipe__name', 'user__username')
    list_display = ('user', 'recipe', 'id')
    list_filter = ('user',)
    autocomplete_fields = ('user', 'recipe')
    list_select_related = ('user', 'recipe', 'recipe__author')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Админка для управления списками покупок."""

    search_fields = ('recipe__name', 'user__username')
    list_display = ('user', 'recipe', 'id')
    list_filter = ('user',)
    autocomplete_fields = ('user', 'recipe')
    list_select_related = ('user', 'recipe', 'recipe__author')
