"""
Пагинация для API приложения Foodgram.

Модуль содержит классы пагинации для контроля
постраничной выдачи ответов API.
"""
from rest_framework.pagination import PageNumberPagination


class LimitPageNumberPagination(PageNumberPagination):
    """
    Пользовательский класс пагинации с параметром лимита.

    Позволяет клиентам указывать размер страницы через параметр
    запроса 'limit'. Максимальный размер страницы ограничен
    6 элементами на страницу.
    """
    page_size_query_param = 'limit'
    max_page_size = 6
