"""Представления API для приложения Foodgram."""

from __future__ import annotations

from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.reverse import reverse

from . import filters, pagination, permissions, serializers
from .models import (
    Favorite,
    Ingredient,
    Recipe,
    ShoppingCart,
    Tag,
)
from .services import RecipeService, UserService

User = get_user_model()

# --------------------------------------------------------------------------- #
# Error messages
# --------------------------------------------------------------------------- #
SELF_SUBSCRIPTION_ERROR = "Нельзя подписаться на самого себя"
ALREADY_SUBSCRIBED_ERROR = "Вы уже подписаны на этого автора"
ALREADY_IN_FAVORITES_ERROR = "Рецепт уже есть в избранном"
ALREADY_IN_CART_ERROR = "Рецепт уже есть в списке покупок"


# --------------------------------------------------------------------------- #
# User management
# --------------------------------------------------------------------------- #
class UserViewSet(DjoserUserViewSet):
    """ViewSet для управления пользователями."""

    def get_permissions(self) -> tuple:
        """Определяет права доступа в зависимости от действия."""
        if self.action in ('me', 'avatar', 'subscriptions', 'subscribe'):
            return (IsAuthenticated(),)
        if self.action == 'retrieve':
            return (AllowAny(),)
        return super().get_permissions()

    @action(
        detail=True,
        methods=('POST', 'DELETE'),
    )
    def subscribe(self, request: Request, id: int) -> Response:
        """Подписка или отписка от автора."""
        author = get_object_or_404(User, pk=id)

        if request.method == 'DELETE':
            was_deleted = UserService.unsubscribe_from_author(
                subscriber=request.user, author=author
            )
            if not was_deleted:
                return Response(status=status.HTTP_404_NOT_FOUND)
            return Response(status=status.HTTP_204_NO_CONTENT)

        subscription, created = UserService.subscribe_to_author(
            subscriber=request.user, author=author
        )

        if not subscription and not created:
            raise ValidationError(dict(error=SELF_SUBSCRIPTION_ERROR))
        if not created:
            raise ValidationError(dict(error=ALREADY_SUBSCRIBED_ERROR))

        serializer = serializers.ReadSubscriptionSerializer(
            author, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=False,
        methods=('GET',),
        pagination_class=pagination.LimitPageNumberPagination,
    )
    def subscriptions(self, request: Request) -> Response:
        """Возвращает список подписок текущего пользователя."""
        authors_queryset = UserService.get_user_subscriptions(
            user=request.user
        )
        paginated_authors = self.paginate_queryset(authors_queryset)
        serializer_instance = serializers.ReadSubscriptionSerializer(
            paginated_authors,
            many=True,
            context={'request': request},
        )
        return self.get_paginated_response(serializer_instance.data)

    @action(
        detail=False,
        methods=('put', 'delete'),
        permission_classes=(IsAuthenticated,),
        url_path='me/avatar',
    )
    def avatar(self, request: Request) -> Response:
        """Управление аватаром текущего пользователя."""
        current_user = request.user

        if request.method == 'DELETE':
            current_user.avatar.delete(save=True)
            return Response(status=HTTPStatus.NO_CONTENT)

        avatar_serializer = serializers.AvatarSerializer(data=request.data)
        avatar_serializer.is_valid(raise_exception=True)
        current_user.avatar = avatar_serializer.validated_data['avatar']
        current_user.save()

        return Response(
            serializers.AvatarSerializer(current_user).data,
            status=HTTPStatus.OK,
        )


# --------------------------------------------------------------------------- #
# Read-only resource viewsets
# --------------------------------------------------------------------------- #
class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для просмотра тегов рецептов."""

    permission_classes = (AllowAny,)
    pagination_class = None
    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для просмотра и поиска ингредиентов."""

    permission_classes = (AllowAny,)
    search_fields = ('^name',)
    filter_backends = (filters.IngredientFilter,)
    pagination_class = None
    serializer_class = serializers.IngredientSerializer
    queryset = Ingredient.objects.all()


# --------------------------------------------------------------------------- #
# Recipe management
# --------------------------------------------------------------------------- #
class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для управления рецептами."""

    filterset_class = filters.RecipeFilterSet
    filter_backends = (DjangoFilterBackend,)
    permission_classes = (permissions.IsAuthorOrReadOnly,)
    queryset = (
        Recipe.objects.select_related('author')
        .prefetch_related('tags', 'ingredients')
        .all()
    )

    def get_serializer_class(self):
        """Выбирает сериализатор в зависимости от метода запроса."""
        return serializers.RecipeSerializer

    def perform_create(self, serializer) -> None:
        """Устанавливает текущего пользователя автором рецепта."""
        # Логика перенесена в RecipeService,
        # который вызывается из сериализатора
        pass

    def _manage_recipe_relation(
        self,
        request: Request,
        pk: int,
        relation_model: type,
        error_msg: str,
    ) -> Response:
        """Универсальный обработчик для избранного и списка покупок."""
        recipe = get_object_or_404(Recipe, pk=pk)

        if request.method == 'DELETE':
            was_deleted = RecipeService.remove_recipe_relation(
                user=request.user, recipe=recipe, relation_model=relation_model
            )
            if not was_deleted:
                return Response(status=status.HTTP_404_NOT_FOUND)
            return Response(status=status.HTTP_204_NO_CONTENT)

        _, created = RecipeService.manage_recipe_relation(
            user=request.user, recipe=recipe, relation_model=relation_model
        )
        if not created:
            raise ValidationError(dict(error=error_msg))

        serializer = serializers.ShortRecipeSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=('POST', 'DELETE'))
    def shopping_cart(self, request: Request, pk: int) -> Response:
        """Добавление/удаление рецепта из списка покупок."""
        return self._manage_recipe_relation(
            request, pk, ShoppingCart, ALREADY_IN_CART_ERROR
        )

    @action(detail=True, methods=('POST', 'DELETE'))
    def favorite(self, request: Request, pk: int) -> Response:
        """Добавление/удаление рецепта из избранного."""
        return self._manage_recipe_relation(
            request, pk, Favorite, ALREADY_IN_FAVORITES_ERROR
        )

    @action(detail=False)
    def download_shopping_cart(self, request: Request) -> FileResponse:
        """Скачивание списка покупок в виде текстового файла."""
        return RecipeService.generate_shopping_cart_file(user=request.user)

    @action(detail=True, url_path='get-link')
    def get_link(self, request: Request, pk: int = None) -> Response:
        """Получение короткой ссылки на рецепт."""
        recipe_instance = get_object_or_404(Recipe, pk=pk)
        short_link = request.build_absolute_uri(
            reverse('short_url', args=(recipe_instance.short_url_code,))
        )
        return Response({'short-link': short_link}, status=status.HTTP_200_OK)
