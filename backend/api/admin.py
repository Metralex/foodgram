from django.contrib import admin
from .models import (
    User, Tag, Ingredient, Recipe, RecipeIngredient,
    Favorite, ShoppingCart, Subscription
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Административная панель для управления пользователями."""

    list_display = ('username', 'email', 'first_name', 'last_name')
    search_fields = ('username', 'email')
    list_filter = ('username', 'email')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Административная панель для управления тегами."""

    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Административная панель для управления ингредиентами."""

    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('name',)


class RecipeIngredientInline(admin.TabularInline):
    """Встроенная панель для ингредиентов рецепта."""

    model = RecipeIngredient
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Административная панель для управления рецептами."""

    list_display = ('name', 'author', 'cooking_time', 'pub_date')
    search_fields = ('name', 'author__username')
    list_filter = ('tags', 'pub_date')
    inlines = [RecipeIngredientInline]
    filter_horizontal = ('tags',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Административная панель для управления избранным."""

    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Административная панель для управления корзиной покупок."""

    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Административная панель для управления подписками."""

    list_display = ('subscriber', 'author')
    search_fields = ('subscriber__username', 'author__username')
