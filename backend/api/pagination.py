from rest_framework.pagination import PageNumberPagination


class LimitPageNumberPagination(PageNumberPagination):
    """Кастомная пагинация с параметром limit вместо page_size."""

    max_page_size = 6
    page_size_query_param = 'limit'
