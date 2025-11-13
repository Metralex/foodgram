"""Конфигурация URL для API Foodgram."""

from __future__ import annotations

from django.urls import URLPattern, URLResolver, include, path

from . import views

app_name = 'api'

# --------------------------------------------------------------------------- #
# URL patterns
# --------------------------------------------------------------------------- #
user_patterns: list[URLPattern | URLResolver] = [
    path(
        'users/subscriptions/',
        views.UserViewSet.as_view({'get': 'subscriptions'}),
        name='user-subscriptions',
    ),
    path(
        'users/<int:id>/subscribe/',
        views.UserViewSet.as_view(
            {'post': 'subscribe', 'delete': 'subscribe'}
        ),
        name='user-subscribe',
    ),
    path(
        'users/me/avatar/',
        views.UserViewSet.as_view({'put': 'avatar', 'delete': 'avatar'}),
        name='user-avatar',
    ),
    path('', include('djoser.urls')),
]

recipe_patterns: list[URLPattern | URLResolver] = [
    path(
        'recipes/download_shopping_cart/',
        views.RecipeViewSet.as_view({'get': 'download_shopping_cart'}),
        name='recipe-download-cart',
    ),
    path(
        'recipes/<int:pk>/shopping_cart/',
        views.RecipeViewSet.as_view(
            {'post': 'shopping_cart', 'delete': 'shopping_cart'}
        ),
        name='recipe-shopping-cart',
    ),
    path(
        'recipes/<int:pk>/favorite/',
        views.RecipeViewSet.as_view(
            {'post': 'favorite', 'delete': 'favorite'}
        ),
        name='recipe-favorite',
    ),
    path(
        'recipes/<int:pk>/get-link/',
        views.RecipeViewSet.as_view({'get': 'get_link'}),
        name='recipe-get-link',
    ),
    path(
        'recipes/',
        views.RecipeViewSet.as_view({'get': 'list', 'post': 'create'}),
        name='recipe-list',
    ),
    path(
        'recipes/<int:pk>/',
        views.RecipeViewSet.as_view(
            {'get': 'retrieve', 'patch': 'update', 'delete': 'destroy'}
        ),
        name='recipe-detail',
    ),
]

resource_patterns: list[URLPattern | URLResolver] = [
    path(
        'tags/',
        views.TagViewSet.as_view({'get': 'list'}),
        name='tag-list',
    ),
    path(
        'tags/<int:pk>/',
        views.TagViewSet.as_view({'get': 'retrieve'}),
        name='tag-detail',
    ),
    path(
        'ingredients/',
        views.IngredientViewSet.as_view({'get': 'list'}),
        name='ingredient-list',
    ),
    path(
        'ingredients/<int:pk>/',
        views.IngredientViewSet.as_view({'get': 'retrieve'}),
        name='ingredient-detail',
    ),
]


urlpatterns: list[URLPattern | URLResolver] = [
    *user_patterns,
    *recipe_patterns,
    *resource_patterns,
    # Authentication endpoints (login, logout, token management)
    path('auth/', include('djoser.urls.authtoken')),
]
