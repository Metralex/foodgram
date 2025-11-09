from rest_framework.pagination import PageNumberPagination


class LimitPageNumberPagination(PageNumberPagination):
    """Пагинация с параметром limit."""

    page_size_query_param = 'limit'
    max_page_size = 6
