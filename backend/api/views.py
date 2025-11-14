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
from rest_framework.response import Response
from rest_framework.reverse import reverse

from . import filters, pagination, permissions, serializers
from .models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from .services import RecipeService, UserService

User = get_user_model()

SELF_SUBSCRIPTION_ERROR = 'Нельзя подписаться на самого себя'
ALREADY_SUBSCRIBED_ERROR = 'Вы уже подписаны на этого автора'
ALREADY_IN_FAVORITES_ERROR = 'Рецепт уже есть в избранном'
ALREADY_IN_CART_ERROR = 'Рецепт уже есть в списке покупок'


class UserViewSet(DjoserUserViewSet):
    """Управление пользователями."""

    def get_permissions(self):
        if self.action in ('me', 'avatar', 'subscriptions', 'subscribe'):
            return (IsAuthenticated(),)
        if self.action == 'retrieve':
            return (AllowAny(),)
        return super().get_permissions()

    @action(detail=True, methods=('POST', 'DELETE'))
    def subscribe(self, request, id):
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
        pagination_class=pagination.LimitPageNumberPagination
    )
    def subscriptions(self, request):
        """Список подписок пользователя."""
        authors_queryset = UserService.get_user_subscriptions(
            user=request.user
        )
        paginated_authors = self.paginate_queryset(authors_queryset)
        serializer_instance = serializers.ReadSubscriptionSerializer(
            paginated_authors, many=True, context={'request': request},
        )
        return self.get_paginated_response(serializer_instance.data)

    @action(
        detail=False,
        methods=('put', 'delete'),
        permission_classes=(IsAuthenticated,),
        url_path='me/avatar',
    )
    def avatar(self, request):
        """Управление аватаром."""
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


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Теги рецептов."""
    permission_classes = (AllowAny,)
    pagination_class = None
    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Ингредиенты."""
    permission_classes = (AllowAny,)
    search_fields = ('^name',)
    filter_backends = (filters.IngredientFilter,)
    pagination_class = None
    serializer_class = serializers.IngredientSerializer
    queryset = Ingredient.objects.all()


class RecipeViewSet(viewsets.ModelViewSet):
    """Управление рецептами."""
    filterset_class = filters.RecipeFilterSet
    filter_backends = (DjangoFilterBackend,)
    permission_classes = (permissions.IsAuthorOrReadOnly,)
    queryset = Recipe.objects.select_related('author').prefetch_related(
        'tags', 'ingredients'
    ).all()

    def get_serializer_class(self):
        return serializers.RecipeSerializer

    def perform_create(self, serializer):
        pass

    def _manage_recipe_relation(self, request, pk, relation_model, error_msg):
        """Добавление/удаление рецепта в избранное или список покупок."""
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
    def shopping_cart(self, request, pk):
        """Добавление/удаление из списка покупок."""
        return self._manage_recipe_relation(
            request, pk, ShoppingCart, ALREADY_IN_CART_ERROR
        )

    @action(detail=True, methods=('POST', 'DELETE'))
    def favorite(self, request, pk):
        """Добавление/удаление из избранного."""
        return self._manage_recipe_relation(
            request, pk, Favorite, ALREADY_IN_FAVORITES_ERROR
        )

    @action(detail=False)
    def download_shopping_cart(self, request):
        """Скачивание списка покупок."""
        return RecipeService.generate_shopping_cart_file(user=request.user)

    @action(detail=True, url_path='get-link')
    def get_link(self, request, pk=None):
        """Получить короткую ссылку на рецепт."""
        recipe_instance = get_object_or_404(Recipe, pk=pk)
        short_link = request.build_absolute_uri(
            reverse('short_url', args=(recipe_instance.short_url_code,))
        )
        return Response({'short-link': short_link}, status=status.HTTP_200_OK)
