"""Функции представлений для работы с рецептами."""

from __future__ import annotations

from django.http import HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404

from .models import Recipe


def short_link_redirect(request, slug):
    """Перенаправляет с короткого кода на полную страницу рецепта."""
    recipe = get_object_or_404(Recipe, short_url_code=slug)
    redirect_url = request.build_absolute_uri(f"/recipes/{recipe.id}/")
    return HttpResponsePermanentRedirect(redirect_url)
