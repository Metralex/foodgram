"""Функции и классы представлений для API эндпоинтов."""
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.reverse import reverse

from accounts.repositories import FollowRepository
from cookbook.models import (
    Category,
    Component,
    CulinaryItem,
    ItemComponent,
)
from cookbook.repositories import (
    BookmarkRepository,
    CulinaryItemRepository,
    WishlistRepository,
)
from gateway import filters, pagination, permissions, serializers, utils

Account = get_user_model()


class AccountEndpoint(DjoserUserViewSet):
    """Обработчик эндпоинта для операций с аккаунтами."""

    def get_permissions(self):
        """Определяет разрешения на основе действия."""
        if self.action == 'me':
            return (IsAuthenticated(),)
        if self.action == 'retrieve':
            return (AllowAny(),)
        return super().get_permissions()

    @action(
        detail=False,
        methods=('put', 'delete'),
        permission_classes=(IsAuthenticated,),
        url_path='me/profile-picture',
    )
    def profile_picture(self, request):
        """Обрабатывает загрузку или удаление фото профиля."""
        account = request.user
        if request.method == 'DELETE':
            account.profile_picture.delete(save=True)
            return Response(status=HTTPStatus.NO_CONTENT)

        serializer = serializers.ProfilePictureSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)
        account.profile_picture = serializer.validated_data[
            'profile_picture'
        ]
        account.save()
        return Response(
            serializers.ProfilePictureSerializer(account).data,
            status=HTTPStatus.OK,
        )

    @action(
        detail=False,
        methods=('GET',),
        pagination_class=pagination.ConfigurablePagePagination,
    )
    def following(self, request):
        """
        Получает аккаунты, на которые подписан текущий пользователь.

        Возвращает постраничный список с кулинарными элементами.
        """
        queryset = FollowRepository.get_following_queryset(request.user)
        serializer = serializers.FollowRelationshipSerializer(
            self.paginate_queryset(queryset),
            many=True,
            context={'request': request},
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=('POST', 'DELETE'),
    )
    def follow(self, request, id):
        """
        Создает или удаляет отношение подписки.

        POST: Подписаться на аккаунт с указанным ID.
        DELETE: Отписаться от аккаунта с указанным ID.
        """
        follower = request.user
        following = get_object_or_404(Account, pk=id)

        if request.method == 'DELETE':
            FollowRepository.delete_follow(follower, following)
            return Response(status=HTTPStatus.NO_CONTENT)

        FollowRepository.create_follow(follower, following)
        return Response(
            serializers.FollowRelationshipSerializer(
                following, context={'request': request}
            ).data,
            status=HTTPStatus.CREATED,
        )


class CategoryEndpoint(viewsets.ReadOnlyModelViewSet):
    """Эндпоинт для данных категорий/классификаций."""
    queryset = Category.objects.all()
    serializer_class = serializers.CategorySerializer
    pagination_class = None
    permission_classes = (AllowAny,)


class ComponentEndpoint(viewsets.ReadOnlyModelViewSet):
    """Эндпоинт для данных компонентов/ингредиентов."""
    queryset = Component.objects.all()
    serializer_class = serializers.ComponentSerializer
    pagination_class = None
    filter_backends = (filters.ComponentSearchFilter,)
    search_fields = ('^name',)
    permission_classes = (AllowAny,)


class CulinaryItemEndpoint(viewsets.ModelViewSet):
    """
    Эндпоинт для операций с кулинарными элементами.

    Предоставляет CRUD операции и специальные действия для элементов.
    Оптимизированный queryset с prefetch_related для производительности.
    """
    permission_classes = (permissions.OwnerOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = filters.CulinaryItemFilterSet

    def get_queryset(self):
        """Получает оптимизированный queryset."""
        account = (
            self.request.user
            if self.request.user.is_authenticated
            else None
        )
        return CulinaryItemRepository.get_optimized_queryset(account)

    def get_serializer_class(self):
        """Возвращает подходящий сериализатор."""
        from rest_framework.permissions import SAFE_METHODS
        if self.request.method in SAFE_METHODS:
            return serializers.CulinaryItemReadSerializer
        return serializers.CulinaryItemWriteSerializer

    def perform_create(self, serializer):
        """Устанавливает текущего пользователя как автора элемента."""
        serializer.save(author=self.request.user)

    @action(detail=True, url_path='share-link')
    def share_link(self, request, pk=None):
        """
        Получает доступную для общего доступа короткую ссылку.

        Возвращает абсолютный URL для короткой ссылки.
        """
        item = get_object_or_404(CulinaryItem, pk=pk)
        short_url = request.build_absolute_uri(
            reverse('short_url', args=(item.short_code,))
        )
        return Response({'short-link': short_url}, status=HTTPStatus.OK)

    @action(detail=False)
    def download_wishlist(self, request):
        """
        Загружает список желаний как текстовый файл.

        Возвращает агрегированный список компонентов и элементов из
        списка желаний пользователя как загружаемый текстовый файл.
        """
        from cookbook.models import WishlistItem

        wishlist_items = WishlistItem.objects.filter(account=request.user)
        item_ids = wishlist_items.values_list('item_id', flat=True)

        components = (
            ItemComponent.objects.filter(item_id__in=item_ids)
            .select_related('component')
            .values(
                'component__name',
                'component__measurement_unit',
            )
            .annotate(quantity=Sum('quantity'))
            .order_by('component__name')
        )
        items = CulinaryItem.objects.filter(id__in=item_ids).distinct()

        file_content = utils.generate_wishlist_file(components, items)
        return FileResponse(
            file_content,
            as_attachment=True,
            filename='wishlist.txt',
            content_type='text/plain',
        )

    @action(detail=True, methods=('POST', 'DELETE'))
    def bookmark(self, request, pk):
        """
        Добавляет или удаляет элемент из закладок.

        POST: Добавить элемент в закладки.
        DELETE: Удалить элемент из закладок.
        """
        item = get_object_or_404(CulinaryItem, pk=pk)

        if request.method == 'DELETE':
            BookmarkRepository.delete(request.user, item)
            return Response(status=HTTPStatus.NO_CONTENT)

        BookmarkRepository.create(request.user, item)
        return Response(
            serializers.CulinaryItemSummarySerializer(item).data,
            status=HTTPStatus.CREATED,
        )

    @action(detail=True, methods=('POST', 'DELETE'))
    def wishlist(self, request, pk):
        """
        Добавляет или удаляет элемент из списка желаний.

        POST: Добавить элемент в список желаний.
        DELETE: Удалить элемент из списка желаний.
        """
        item = get_object_or_404(CulinaryItem, pk=pk)

        if request.method == 'DELETE':
            WishlistRepository.delete(request.user, item)
            return Response(status=HTTPStatus.NO_CONTENT)

        WishlistRepository.create(request.user, item)
        return Response(
            serializers.CulinaryItemSummarySerializer(item).data,
            status=HTTPStatus.CREATED,
        )
