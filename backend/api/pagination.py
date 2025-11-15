"""Классы пагинации для API Foodgram."""

from __future__ import annotations

from rest_framework.pagination import PageNumberPagination

from backend.settings import MAX_PAGE_SIZE


class LimitPageNumberPagination(PageNumberPagination):
    """Пагинация."""

    max_page_size = MAX_PAGE_SIZE
    page_size_query_param = "limit"
