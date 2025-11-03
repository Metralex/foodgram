"""
API pagination for foodgram application.

This module contains pagination classes for controlling
how API responses are paginated.
"""
from rest_framework.pagination import PageNumberPagination


class LimitPageNumberPagination(PageNumberPagination):
    """
    Custom pagination class with limit parameter.

    Allows clients to specify page size via 'limit' query parameter.
    Maximum page size is limited to 6 items per page.
    """
    page_size_query_param = 'limit'
    max_page_size = 6
