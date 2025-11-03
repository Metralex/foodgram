"""
API views for foodgram application.

This module contains ViewSets for handling HTTP requests
and delegating business logic to service classes.
"""
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS, AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.reverse import reverse

from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)

from . import filters, pagination, permissions, serializers, services, utils


User = get_user_model()


class UserViewSet(DjoserUserViewSet):
    def get_permissions(self):
        if self.action == 'me':
            return (IsAuthenticated(),)
        if self.action == 'retrieve':
            return (AllowAny(),)
        return super().get_permissions()

    @action(
        detail=False,
        methods=('put', 'delete'),
        permission_classes=(IsAuthenticated,),
        url_path='me/avatar',
    )
    def avatar(self, request):
        user = request.user
        if request.method == 'DELETE':
            user.avatar.delete(save=True)
            return Response(status=HTTPStatus.NO_CONTENT)
        serializer = serializers.AvatarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.avatar = serializer.validated_data['avatar']
        user.save()
        return Response(
            serializers.AvatarSerializer(user).data,
            status=HTTPStatus.OK,
        )

    @action(
        detail=False,
        methods=('GET',),
        pagination_class=pagination.LimitPageNumberPagination,
    )
    def subscriptions(self, request):
        """
        Get list of users that the current user is subscribed to.

        Returns paginated list of users with their recipes.
        """
        queryset = services.SubscriptionService.get_subscriptions_queryset(
            request.user
        )
        serializer = serializers.ReadSubscriptionSerializer(
            self.paginate_queryset(queryset),
            many=True,
            context={'request': request},
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=('POST', 'DELETE'),
    )
    def subscribe(self, request, id):
        """
        Subscribe or unsubscribe to a user.

        POST: Create subscription to user with given id.
        DELETE: Remove subscription to user with given id.
        """
        subscriber = request.user
        author = get_object_or_404(User, pk=id)

        if request.method == 'DELETE':
            services.SubscriptionService.unsubscribe(subscriber, author)
            return Response(status=HTTPStatus.NO_CONTENT)

        services.SubscriptionService.subscribe(subscriber, author)
        return Response(
            serializers.ReadSubscriptionSerializer(
                author, context={'request': request}
            ).data,
            status=HTTPStatus.CREATED,
        )


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = serializers.TagSerializer
    pagination_class = None
    permission_classes = (AllowAny,)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = serializers.IngredientSerializer
    pagination_class = None
    filter_backends = (filters.IngredientFilter,)
    search_fields = ('^name',)
    permission_classes = (AllowAny,)


class RecipeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for recipe operations.

    Provides CRUD operations and custom actions for recipes.
    Optimized queryset with prefetch_related for better performance.
    """
    permission_classes = (permissions.IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = filters.RecipeFilterSet

    def get_queryset(self):
        """
        Get queryset with optimizations for list/detail views.

        Prefetches related objects to minimize database queries.
        """
        queryset = (
            Recipe.objects
            .select_related('author')
            .prefetch_related(
                'tags',
                'ingredients',
                'recipeingredients__ingredient'
            )
        )

        # Prefetch user-specific data if authenticated
        user = self.request.user
        if user.is_authenticated:
            from django.db.models import Prefetch
            queryset = queryset.prefetch_related(
                Prefetch(
                    'favorites',
                    queryset=Favorite.objects.filter(user=user),
                    to_attr='_user_favorites'
                ),
                Prefetch(
                    'shoppingcarts',
                    queryset=ShoppingCart.objects.filter(user=user),
                    to_attr='_user_shopping_carts'
                )
            )
        return queryset

    def get_serializer_class(self):
        """Return appropriate serializer based on request method."""
        if self.request.method in SAFE_METHODS:
            return serializers.ReadRecipeSerializer
        return serializers.WriteRecipeSerializer

    def perform_create(self, serializer):
        """Set recipe author to current user on creation."""
        serializer.save(author=self.request.user)

    @action(detail=True, url_path='get-link')
    def get_link(self, request, pk=None):
        """
        Get short URL link for recipe.

        Returns absolute URL for recipe's short link.
        """
        recipe = get_object_or_404(Recipe, pk=pk)
        short_url = request.build_absolute_uri(
            reverse('short_url', args=(recipe.short_url_code,))
        )
        return Response({'short-link': short_url}, status=HTTPStatus.OK)

    @action(detail=False)
    def download_shopping_cart(self, request):
        """
        Download shopping cart as text file.

        Returns aggregated ingredients and recipe list from user's
        shopping cart as downloadable text file.
        """
        ingredients = (
            RecipeIngredient.objects.filter(
                recipe__shoppingcarts__user=request.user
            )
            .select_related('ingredient')
            .values(
                'ingredient__name',
                'ingredient__measurement_unit',
            )
            .annotate(amount=Sum('amount'))
            .order_by('ingredient__name')
        )
        recipes = Recipe.objects.filter(
            shoppingcarts__user=request.user
        ).distinct()
        file_content = utils.make_shopping_cart_file(ingredients, recipes)
        return FileResponse(
            file_content,
            as_attachment=True,
            filename='shopping_cart.txt',
            content_type='text/plain',
        )

    @action(detail=True, methods=('POST', 'DELETE'))
    def favorite(self, request, pk):
        """
        Add or remove recipe from favorites.

        POST: Add recipe to favorites.
        DELETE: Remove recipe from favorites.
        """
        recipe = get_object_or_404(Recipe, pk=pk)

        if request.method == 'DELETE':
            services.RecipeInteractionService.remove_from_favorites(
                request.user, recipe
            )
            return Response(status=HTTPStatus.NO_CONTENT)

        services.RecipeInteractionService.add_to_favorites(
            request.user, recipe
        )
        return Response(
            serializers.ShortRecipeSerializer(recipe).data,
            status=HTTPStatus.CREATED,
        )

    @action(detail=True, methods=('POST', 'DELETE'))
    def shopping_cart(self, request, pk):
        """
        Add or remove recipe from shopping cart.

        POST: Add recipe to shopping cart.
        DELETE: Remove recipe from shopping cart.
        """
        recipe = get_object_or_404(Recipe, pk=pk)

        if request.method == 'DELETE':
            services.RecipeInteractionService.remove_from_shopping_cart(
                request.user, recipe
            )
            return Response(status=HTTPStatus.NO_CONTENT)

        services.RecipeInteractionService.add_to_shopping_cart(
            request.user, recipe
        )
        return Response(
            serializers.ShortRecipeSerializer(recipe).data,
            status=HTTPStatus.CREATED,
        )
