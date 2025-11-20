"""Конфигурация Django admin для пользователей."""

from admin_auto_filters.filters import AutocompleteFilter

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Subscription, User


class SubscriberFilter(AutocompleteFilter):
    """Фильтр по подписчику с автодополнением."""

    title = 'Подписчик'
    field_name = 'subscriber'


class AuthorFilter(AutocompleteFilter):
    """Фильтр по автору с автодополнением."""

    title = 'Автор'
    field_name = 'author'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Админка для управления пользователями."""

    list_filter = BaseUserAdmin.list_filter + ('email',)
    search_fields = ('email', 'username', 'first_name', 'last_name')
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_staff')
    ordering = ('username',)

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Дополнительная информация', {'fields': ('avatar',)}),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (
            'Дополнительная информация',
            {'fields': ('first_name', 'last_name', 'avatar')},
        ),
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Админка для управления подписками."""

    search_fields = ('author__username', 'subscriber__username')
    list_display = ('subscriber', 'author', 'id')
    list_filter = [SubscriberFilter, AuthorFilter]
    autocomplete_fields = ('subscriber', 'author')
    list_select_related = ('subscriber', 'author')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('subscriber', 'author')
