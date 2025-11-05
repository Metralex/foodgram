"""Представления для функциональности cookbook."""
from django.http import HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404

from .models import CulinaryItem


def short_link_redirect(request, code):
    """
    Перенаправляет с короткого кода на полную страницу кулинарного элемента.

    Функциональное представление для обработки коротких ссылок,
    обеспечивающее чистое разделение от API слоя.
    """
    item = get_object_or_404(CulinaryItem, short_code=code)
    redirect_url = request.build_absolute_uri(
        f'/recipes/{item.id}/'
    )
    return HttpResponsePermanentRedirect(redirect_url)
