"""Корневые объявления URL для бэкенда Foodgram."""

from __future__ import annotations

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import URLPattern, URLResolver, include, path

from api.views_recipe import short_link_redirect


def _static_patterns() -> list[URLPattern]:
    """Составить правила обслуживания статических файлов и медиа, используемые
    во время разработки."""
    if not settings.DEBUG:
        return []
    return [
        *static(settings.STATIC_URL, document_root=settings.STATIC_ROOT),
        *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
    ]


urlpatterns: list[URLPattern | URLResolver] = [
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
    path("s/<slug>/", short_link_redirect, name="short_url"),
    *_static_patterns(),
]
