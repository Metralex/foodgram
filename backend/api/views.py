from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
from typing import Iterable, Tuple, Type

from django.contrib.auth import get_user_model
from django.db.models import QuerySet, Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as BaseUserViewSet
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


@dataclass(frozen=True)
class RelationRules:
    model: Type
    duplicate_message: str


def _create_or_remove_recipe_relation(
    rules: RelationRules,
    request,
    recipe_id: int,
) -> Response:
    recipe = get_object_or_404(Recipe, pk=recipe_id)
    relation_manager = rules.model.objects

    if request.method == "DELETE":
        get_object_or_404(
            rules.model, user=request.user, recipe=recipe
        ).delete()
        return Response(status=HTTPStatus.NO_CONTENT)

    _, created = relation_manager.get_or_create(
        user=request.user, recipe=recipe
    )
    if not created:
        raise ValidationError({"error": rules.duplicate_message})
    payload = serializers.ShortRecipeSerializer(recipe).data
    return Response(payload, status=HTTPStatus.CREATED)


def _aggregate_ingredients(user) -> Iterable[dict]:
    return (
        RecipeIngredient.objects.filter(recipe__shoppingcarts__user=user)
        .select_related("recipe", "ingredient")
        .values(
            "ingredient__name",
            "ingredient__measurement_unit",
        )
        .annotate(amount=Sum("amount"))
        .order_by("ingredient__name")
    )


class UserViewSet(BaseUserViewSet):
    """Extend Djoser behaviour with avatar and subscription features."""

    permission_overrides: dict[str, Tuple] = {
        "me": (IsAuthenticated(),),
        "retrieve": (AllowAny(),),
    }

    def get_permissions(self):
        override = self.permission_overrides.get(self.action)
        if override is not None:
            return override
        return super().get_permissions()

    def _serializer_context(self):
        return {"request": self.request}

    @action(
        detail=False,
        methods=("put", "delete"),
        permission_classes=(IsAuthenticated,),
        url_path="me/avatar",
    )
    def avatar(self, request):
        user = request.user
        if request.method == "DELETE":
            user.avatar.delete(save=True)
            return Response(status=HTTPStatus.NO_CONTENT)

        serializer = serializers.AvatarSerializer(
            data=request.data, context=self._serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        user.avatar = serializer.validated_data["avatar"]
        user.save(update_fields=["avatar"])
        return Response(
            serializers.AvatarSerializer(
                user, context=self._serializer_context()
            ).data,
            status=HTTPStatus.OK,
        )

    @action(
        detail=False,
        methods=("get",),
        pagination_class=pagination.LimitPageNumberPagination,
    )
    def subscriptions(self, request):
        queryset = User.objects.filter(authors__subscriber=request.user)
        page = self.paginate_queryset(queryset)
        serializer = serializers.ReadSubscriptionSerializer(
            page,
            many=True,
            context=self._serializer_context(),
        )
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=("post", "delete"))
    def subscribe(self, request, id):
        subscriber = request.user
        author = get_object_or_404(User, pk=id)

        if request.method == "DELETE":
            get_object_or_404(
                Subscription, author=author, subscriber=subscriber
            ).delete()
            return Response(status=HTTPStatus.NO_CONTENT)

        if subscriber == author:
            raise ValidationError(
                {"error": "Нельзя подписаться на самого себя"}
            )

        _, created = Subscription.objects.get_or_create(
            author=author, subscriber=subscriber
        )
        if not created:
            raise ValidationError(
                {"error": "Вы уже подписаны на этого автора"}
            )

        serializer = serializers.ReadSubscriptionSerializer(
            author, context=self._serializer_context()
        )
        return Response(serializer.data, status=HTTPStatus.CREATED)


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
    search_fields = ("^name",)
    permission_classes = (AllowAny,)


class RecipeViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = filters.RecipeFilterSet

    def get_queryset(self) -> QuerySet:
        base_queryset = Recipe.objects.select_related(
            "author"
        ).prefetch_related(
            "tags", "ingredients"
        )
        return base_queryset

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return serializers.ReadRecipeSerializer
        return serializers.WriteRecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, url_path="get-link")
    def get_link(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        short_url = request.build_absolute_uri(
            reverse("short_url", args=(recipe.short_url_code,))
        )
        return Response({"short-link": short_url}, status=HTTPStatus.OK)

    @action(detail=False)
    def download_shopping_cart(self, request):
        ingredients = _aggregate_ingredients(request.user)
        recipes = Recipe.objects.filter(
            shoppingcarts__user=request.user
        ).distinct()
        return FileResponse(
            utils.make_shopping_cart_file(ingredients, recipes),
            as_attachment=True,
            filename="shopping_cart.txt",
            content_type="text/plain",
        )

    @action(detail=True, methods=("post", "delete"))
    def favorite(self, request, pk):
        rules = RelationRules(
            model=Favorite,
            duplicate_message="Рецепт уже есть в избранном",
        )
        return _create_or_remove_recipe_relation(rules, request, pk)

    @action(detail=True, methods=("post", "delete"))
    def shopping_cart(self, request, pk):
        rules = RelationRules(
            model=ShoppingCart,
            duplicate_message="Рецепт уже есть в списке покупок",
        )
        return _create_or_remove_recipe_relation(rules, request, pk)
