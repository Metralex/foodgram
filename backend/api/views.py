from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.db.models import BooleanField, Exists, OuterRef, Value
from django.http import HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.reverse import reverse
from users.models import Subscription

from . import filters, pagination, permissions, serializers

User = get_user_model()
SELF_SUBSCRIPTION_ERROR = 'Нельзя подписаться на самого себя'
ALREADY_SUBSCRIBED_ERROR = 'Вы уже подписаны на этого автора'
ALREADY_IN_CART_ERROR = 'Рецепт уже есть в списке покупок'
ALREADY_IN_FAVORITES_ERROR = 'Рецепт уже есть в избранном'


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
            deleted_count, _ = Subscription.objects.filter(
                subscriber=request.user, author=author
            ).delete()
            if not deleted_count:
                return Response(status=status.HTTP_404_NOT_FOUND)
            return Response(status=status.HTTP_204_NO_CONTENT)

        # Создаем через сериализатор
        subscription_serializer = serializers.SubscriptionSerializer(
            data={'subscriber': request.user.id, 'author': author.id}
        )
        subscription_serializer.is_valid(raise_exception=True)
        subscription_serializer.save()

        # Возвращаем данные автора
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
        authors_queryset = User.objects.filter(
            authors__subscriber=request.user
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
    serializer_class = serializers.RecipeSerializer

    def get_queryset(self):
        """Возвращает queryset с аннотациями."""
        user = self.request.user
        queryset = Recipe.objects.select_related('author').prefetch_related(
            'tags', 'ingredients'
        )

        if user.is_authenticated:
            queryset = queryset.annotate(
                is_favorited=Exists(
                    Favorite.objects.filter(
                        user=user, recipe=OuterRef('pk')
                    )
                )
            )
            queryset = queryset.annotate(
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects.filter(
                        user=user, recipe=OuterRef('pk')
                    )
                )
            )
        else:
            queryset = queryset.annotate(
                is_favorited=Value(
                    False, output_field=BooleanField()
                )
            )
            queryset = queryset.annotate(
                is_in_shopping_cart=Value(
                    False, output_field=BooleanField()
                )
            )

        return queryset

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
        from django.db.models import Sum
        from django.http import FileResponse
        from recipes import utils

        ingredients = (
            RecipeIngredient.objects.filter(
                recipe__shoppingcarts__user=request.user
            )
            .select_related('recipe', 'ingredient')
            .values('ingredient__name', 'ingredient__measurement_unit')
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

    @action(detail=True, url_path='get-link')
    def get_link(self, request, pk=None):
        """Получить короткую ссылку на рецепт."""
        recipe_instance = get_object_or_404(Recipe, pk=pk)
        short_link = request.build_absolute_uri(
            reverse('short_url', args=(recipe_instance.short_url_code,))
        )
        return Response({'short-link': short_link}, status=status.HTTP_200_OK)


def short_link_redirect(request, slug):
    """Перенаправляет с короткого кода на полную страницу рецепта."""
    recipe = get_object_or_404(Recipe, short_url_code=slug)
    redirect_url = request.build_absolute_uri(f"/recipes/{recipe.id}/")
    return HttpResponsePermanentRedirect(redirect_url)
