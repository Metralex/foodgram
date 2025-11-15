"""Конфигурация Django admin для рецептов."""

from django.contrib import admin

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Админка для управления тегами рецептов."""

    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)
    list_display = ("slug", "name")
    ordering = ("name",)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Админка для управления ингредиентами."""

    list_filter = ("measurement_unit",)
    search_fields = ("name",)
    list_display = ("name", "measurement_unit")
    ordering = ("name",)


class RecipeIngredientInline(admin.TabularInline):
    """Inline редактор для ингредиентов рецепта."""

    extra = 1
    model = RecipeIngredient
    autocomplete_fields = ("ingredient",)
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Админка для управления рецептами."""

    filter_horizontal = ("tags",)
    inlines = [RecipeIngredientInline]
    list_filter = ("pub_date", "tags", "author")
    search_fields = ("author__username", "name", "text")
    list_display = (
        "name",
        "author",
        "pub_date",
        "cooking_time",
        "get_favorites_count",
    )
    readonly_fields = ("pub_date", "short_url_code", "get_favorites_count")
    ordering = ("-pub_date",)

    def get_favorites_count(self, obj: Recipe) -> int:
        """Возвращает количество добавлений в избранное."""
        return obj.favorites.count()

    get_favorites_count.short_description = "Добавлений в избранное"


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Админка для управления избранными рецептами."""

    search_fields = ("recipe__name", "user__username")
    list_display = ("user", "recipe", "id")
    list_filter = ("user",)
    autocomplete_fields = ("user", "recipe")


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Админка для управления списками покупок."""

    search_fields = ("recipe__name", "user__username")
    list_display = ("user", "recipe", "id")
    list_filter = ("user",)
    autocomplete_fields = ("user", "recipe")
