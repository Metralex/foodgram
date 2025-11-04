"""
Служебные функции для API приложения Foodgram.

Модуль содержит вспомогательные функции для генерации файлов,
форматирования данных и других вспомогательных операций.
"""
from io import BytesIO
from typing import Iterable, List

from django.utils import timezone

TIME_FORMAT = '%d-%m-%Y %H:%M'


def make_shopping_cart_file(
    ingredients: Iterable[dict], recipes: Iterable
) -> BytesIO:
    """
    Сгенерировать содержимое текстового файла списка покупок.

    Создаёт отформатированный текстовый документ, содержащий
    агрегированные ингредиенты и список рецептов из списка покупок
    пользователя.

    Аргументы:
        ingredients: Итерируемый объект словарей ингредиентов с ключами:
                     ingredient__name, ingredient__measurement_unit, amount
        recipes: Итерируемый объект экземпляров Recipe

    Возвращает:
        BytesIO: Буфер, содержащий отформатированный текстовый документ
    """
    current_time = timezone.now().strftime(TIME_FORMAT)

    # Форматируем список ингредиентов
    ingredient_lines = [
        f'{index}. {item["ingredient__name"].capitalize()} '
        f'({item["ingredient__measurement_unit"]}) - '
        f'{item["amount"]}'
        for index, item in enumerate(ingredients, start=1)
    ]

    # Форматируем список рецептов
    recipe_lines = [
        f'{index}. {recipe.name}'
        for index, recipe in enumerate(recipes, start=1)
    ]

    # Объединяем все секции
    document_lines: List[str] = [
        f'Дата и время: {current_time}',
        '',
        'Список покупок:',
        *ingredient_lines,
        '',
        'Список рецептов:',
        *recipe_lines,
    ]

    document_text = '\n'.join(document_lines)
    return BytesIO(document_text.encode('utf-8'))
