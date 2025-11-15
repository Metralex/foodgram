"""Конфигурация Django admin для пользователей."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Subscription, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Админка для управления пользователями."""

    list_filter = BaseUserAdmin.list_filter + ("email",)
    search_fields = ("email", "username", "first_name", "last_name")
    list_display = ("email", "username", "first_name", "last_name", "is_staff")
    ordering = ("username",)

    fieldsets = BaseUserAdmin.fieldsets + (
        ("Дополнительная информация", {"fields": ("avatar",)}),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Дополнительная информация", {"fields": (
            "first_name", "last_name", "avatar")}),
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Админка для управления подписками."""

    search_fields = ("author__username", "subscriber__username")
    list_display = ("subscriber", "author", "id")
    list_filter = ("subscriber", "author")
    autocomplete_fields = ("subscriber", "author")
