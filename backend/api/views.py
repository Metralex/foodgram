"""
Обработчики HTTP запросов для API приложения Foodgram.

Модуль содержит ViewSet'ы для обработки HTTP запросов
и делегирования бизнес-логики классам-сервисам.
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


class UserHandler(DjoserUserViewSet):
    """Обработчик операций с пользователями."""

    def get_permissions(self):
        """Получить разрешения в зависимости от действия."""
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
        """Загрузить или удалить аватар пользователя."""
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
        Получить список подписок текущего пользователя.

        Возвращает постраничный список авторов с их рецептами.
        """
        queryset = services.FollowingProvider.get_subscriptions_queryset(
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
        Подписаться или отписаться от автора.

        POST: Создать подписку на автора с заданным id.
        DELETE: Удалить подписку на автора с заданным id.
        """
        subscriber = request.user
        author = get_object_or_404(User, pk=id)

        if request.method == 'DELETE':
            services.FollowingProvider.unsubscribe(subscriber, author)
            return Response(status=HTTPStatus.NO_CONTENT)

        services.FollowingProvider.subscribe(subscriber, author)
        return Response(
            serializers.ReadSubscriptionSerializer(
                author, context={'request': request}
            ).data,
            status=HTTPStatus.CREATED,
        )


class ClassificationHandler(viewsets.ReadOnlyModelViewSet):
    """Обработчик для работы с категориями блюд (теги)."""
    queryset = Tag.objects.all()
    serializer_class = serializers.TagSerializer
    pagination_class = None
    permission_classes = (AllowAny,)


class ElementHandler(viewsets.ReadOnlyModelViewSet):
    """Обработчик для работы с ингредиентами."""
    queryset = Ingredient.objects.all()
    serializer_class = serializers.IngredientSerializer
    pagination_class = None
    filter_backends = (filters.IngredientFilter,)
    search_fields = ('^name',)
    permission_classes = (AllowAny,)


class DishHandler(viewsets.ModelViewSet):
    """
    Обработчик для операций с блюдами (рецептами).

    Предоставляет CRUD операции и специальные действия для блюд.
    Оптимизированный queryset с prefetch_related для улучшения
    производительности.
    """
    permission_classes = (permissions.IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = filters.RecipeFilterSet

    def get_queryset(self):
        """
        Получить queryset с оптимизациями для представлений
        списка и деталей.

        Предварительно загружает связанные объекты для минимизации
        запросов БД.
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

        # Предварительно загружаем данные, специфичные для пользователя
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
        """Возвращает сериализатор в зависимости от типа запроса."""
        if self.request.method in SAFE_METHODS:
            return serializers.ReadRecipeSerializer
        return serializers.WriteRecipeSerializer

    def perform_create(self, serializer):
        """Установить текущего пользователя как автора блюда."""
        serializer.save(author=self.request.user)

    @action(detail=True, url_path='get-link')
    def get_link(self, request, pk=None):
        """
        Получить короткую URL ссылку для блюда.

        Возвращает абсолютный URL короткой ссылки блюда.
        """
        recipe = get_object_or_404(Recipe, pk=pk)
        short_url = request.build_absolute_uri(
            reverse('short_url', args=(recipe.short_url_code,))
        )
        return Response({'short-link': short_url}, status=HTTPStatus.OK)

    @action(detail=False)
    def download_shopping_cart(self, request):
        """
        Скачать список покупок в виде текстового файла.

        Возвращает агрегированный список ингредиентов и рецептов
        из корзины покупок пользователя в виде загружаемого
        текстового файла.
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
        file_content = utils.make_shopping_cart_file(
            ingredients, recipes
        )
        return FileResponse(
            file_content,
            as_attachment=True,
            filename='shopping_cart.txt',
            content_type='text/plain',
        )

    @action(detail=True, methods=('POST', 'DELETE'))
    def favorite(self, request, pk):
        """
        Добавить или удалить блюдо из избранного.

        POST: Добавить блюдо в избранное.
        DELETE: Удалить блюдо из избранного.
        """
        recipe = get_object_or_404(Recipe, pk=pk)

        if request.method == 'DELETE':
            services.RecipeInteractionProvider.remove_from_favorites(
                request.user, recipe
            )
            return Response(status=HTTPStatus.NO_CONTENT)

        services.RecipeInteractionProvider.add_to_favorites(
            request.user, recipe
        )
        return Response(
            serializers.ShortRecipeSerializer(recipe).data,
            status=HTTPStatus.CREATED,
        )

    @action(detail=True, methods=('POST', 'DELETE'))
    def shopping_cart(self, request, pk):
        """
        Добавить или удалить блюдо из списка покупок.

        POST: Добавить блюдо в список покупок.
        DELETE: Удалить блюдо из списка покупок.
        """
        recipe = get_object_or_404(Recipe, pk=pk)

        if request.method == 'DELETE':
            services.RecipeInteractionProvider.remove_from_shopping_cart(
                request.user, recipe
            )
            return Response(status=HTTPStatus.NO_CONTENT)

        services.RecipeInteractionProvider.add_to_shopping_cart(
            request.user, recipe
        )
        return Response(
            serializers.ShortRecipeSerializer(recipe).data,
            status=HTTPStatus.CREATED,
        )
