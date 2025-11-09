from django.contrib import admin

from .models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Subscription,
    Tag,
    User,
)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Админка для управления тегами рецептов."""

    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    list_display = ('slug', 'name')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Админка для управления ингредиентами."""

    list_filter = ('measurement_unit',)
    search_fields = ('name',)
    list_display = ('name', 'measurement_unit')


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Админка для управления пользователями системы."""

    list_filter = ('email', 'username')
    search_fields = ('email', 'username')
    list_display = ('email', 'username', 'first_name', 'last_name')


class RecipeIngredientInline(admin.TabularInline):
    """Inline редактор для ингредиентов в рецепте."""

    extra = 1
    model = RecipeIngredient


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Админка для управления рецептами."""

    filter_horizontal = ('tags',)
    inlines = [RecipeIngredientInline]
    list_filter = ('pub_date', 'tags')
    search_fields = ('author__username', 'name')
    list_display = ('name', 'author', 'pub_date', 'cooking_time')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Админка для управления подписками пользователей."""

    search_fields = ('author__username', 'subscriber__username')
    list_display = ('subscriber', 'author')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Админка для управления избранными рецептами."""

    search_fields = ('recipe__name', 'user__username')
    list_display = ('user', 'recipe')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Админка для управления списками покупок."""

    search_fields = ('recipe__name', 'user__username')
    list_display = ('user', 'recipe')
