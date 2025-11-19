"""Классы пагинации для API Foodgram."""

from rest_framework.pagination import PageNumberPagination

from django.conf import settings


class LimitPageNumberPagination(PageNumberPagination):

    """Пагинация."""

    max_page_size = settings.MAX_PAGE_SIZE
    page_size_query_param = 'limit'
