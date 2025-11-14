"""Классы пагинации для API Foodgram."""

from __future__ import annotations

from rest_framework.pagination import PageNumberPagination


class LimitPageNumberPagination(PageNumberPagination):
    """Пагинация."""

    max_page_size = 6
    page_size_query_param = "limit"
