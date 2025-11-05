"""Pagination configuration for API responses."""
from rest_framework.pagination import PageNumberPagination


class ConfigurablePagePagination(PageNumberPagination):
    """
    Configurable pagination with client-specified page size.

    Allows clients to control page size through query parameters
    while enforcing a maximum limit for performance.
    """
    page_size_query_param = 'limit'
    max_page_size = 6
    page_size = 6
