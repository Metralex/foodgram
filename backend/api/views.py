from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import SAFE_METHODS, AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.reverse import reverse

from . import filters, pagination, permissions, serializers, utils
from .models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Subscription,
    Tag,
)

User = get_user_model()

SELF_SUBSCRIPTION_ERROR = 'Нельзя подписаться на самого себя'
ALREADY_SUBSCRIBED_ERROR = 'Вы уже подписаны на этого автора'
ALREADY_IN_FAVORITES_ERROR = 'Рецепт уже есть в избранном'
ALREADY_IN_CART_ERROR = 'Рецепт уже есть в списке покупок'


class UserViewSet(DjoserUserViewSet):
    """ViewSet для работы с пользователями, включая аватары и подписки."""

    def get_permissions(self):
        if self.action in ('me', 'avatar', 'subscriptions', 'subscribe'):
            return (IsAuthenticated(),)
        if self.action == 'retrieve':
            return (AllowAny(),)
        return super().get_permissions()

    @action(
        detail=True,
        methods=('POST', 'DELETE'),
    )
    def subscribe(self, request, id):
        """Подписка и отписка от автора."""
        current_user = request.user
        target_author = get_object_or_404(User, pk=id)

        if request.method == 'DELETE':
            subscription_instance = get_object_or_404(
                Subscription,
                author=target_author,
                subscriber=current_user
            )
            subscription_instance.delete()
            return Response(status=HTTPStatus.NO_CONTENT)

        if current_user == target_author:
            raise ValidationError(dict(error=SELF_SUBSCRIPTION_ERROR))

        subscription_instance, was_created = (
            Subscription.objects.get_or_create(
                author=target_author, subscriber=current_user
            )
        )
        if not was_created:
            raise ValidationError(dict(error=ALREADY_SUBSCRIBED_ERROR))

        return Response(
            serializers.ReadSubscriptionSerializer(
                target_author, context={'request': request}
            ).data,
            status=HTTPStatus.CREATED,
        )

    @action(
        detail=False,
        methods=('GET',),
        pagination_class=pagination.LimitPageNumberPagination,
    )
    def subscriptions(self, request):
        """Список подписок текущего пользователя."""
        authors_queryset = User.objects.filter(
            authors__subscriber=request.user
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
    def avatar(self, request):
        """Управление аватаром пользователя."""
        current_user = request.user

        if request.method == 'DELETE':
            current_user.avatar.delete(save=True)
            return Response(status=HTTPStatus.NO_CONTENT)

        avatar_serializer = serializers.AvatarSerializer(
            data=request.data
        )
        avatar_serializer.is_valid(raise_exception=True)
        current_user.avatar = avatar_serializer.validated_data['avatar']
        current_user.save()

        return Response(
            serializers.AvatarSerializer(current_user).data,
            status=HTTPStatus.OK,
        )


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint для просмотра тегов."""

    permission_classes = (AllowAny,)
    pagination_class = None
    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint для просмотра и поиска ингредиентов."""

    permission_classes = (AllowAny,)
    search_fields = ('^name',)
    filter_backends = (filters.IngredientFilter,)
    pagination_class = None
    serializer_class = serializers.IngredientSerializer
    queryset = Ingredient.objects.all()


class RecipeViewSet(viewsets.ModelViewSet):
    """API endpoint для управления рецептами."""

    filterset_class = filters.RecipeFilterSet
    filter_backends = (DjangoFilterBackend,)
    permission_classes = (permissions.IsAuthorOrReadOnly,)
    queryset = (
        Recipe.objects.select_related('author')
        .prefetch_related('tags', 'ingredients')
        .all()
    )

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return serializers.ReadRecipeSerializer
        return serializers.WriteRecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def _manage_recipe_relation(
        self, request, pk, relation_model, error_msg
    ):
        """Универсальный метод для избранного/корзины."""
        recipe_instance = get_object_or_404(Recipe, pk=pk)

        if request.method == 'DELETE':
            relation_instance = get_object_or_404(
                relation_model,
                recipe=recipe_instance,
                user=request.user
            )
            relation_instance.delete()
            return Response(status=HTTPStatus.NO_CONTENT)

        relation_instance, was_created = (
            relation_model.objects.get_or_create(
                user=request.user, recipe=recipe_instance
            )
        )
        if not was_created:
            raise ValidationError(dict(error=error_msg))

        return Response(
            serializers.ShortRecipeSerializer(recipe_instance).data,
            status=HTTPStatus.CREATED,
        )

    @action(detail=True, methods=('POST', 'DELETE'))
    def shopping_cart(self, request, pk):
        """Добавление/удаление рецепта в список покупок."""
        return self._manage_recipe_relation(
            request, pk, ShoppingCart, ALREADY_IN_CART_ERROR
        )

    @action(detail=True, methods=('POST', 'DELETE'))
    def favorite(self, request, pk):
        """Добавление/удаление рецепта в избранное."""
        return self._manage_recipe_relation(
            request, pk, Favorite, ALREADY_IN_FAVORITES_ERROR
        )

    @action(detail=False)
    def download_shopping_cart(self, request):
        """Скачивание списка покупок в текстовом формате."""
        aggregated_ingredients = (
            RecipeIngredient.objects.filter(
                recipe__shoppingcarts__user=request.user
            )
            .select_related('recipe', 'ingredient')
            .values(
                'ingredient__name',
                'ingredient__measurement_unit',
            )
            .annotate(amount=Sum('amount'))
            .order_by('ingredient__name')
        )
        related_recipes = Recipe.objects.filter(
            shoppingcarts__user=request.user
        ).distinct()

        file_content = utils.make_shopping_cart_file(
            aggregated_ingredients, related_recipes
        )
        return FileResponse(
            file_content,
            as_attachment=True,
            filename='shopping_cart.txt',
            content_type='text/plain',
        )

    @action(detail=True, url_path='get-link')
    def get_link(self, request, pk=None):
        """Получение короткой ссылки на рецепт."""
        recipe_instance = get_object_or_404(Recipe, pk=pk)
        short_link = request.build_absolute_uri(
            reverse('short_url', args=(recipe_instance.short_url_code,))
        )
        return Response({'short-link': short_link}, status=HTTPStatus.OK)
