"""
API utility functions for foodgram application.

This module contains utility functions for generating files,
formatting data, and other helper operations.
"""
from io import BytesIO
from typing import Iterable, List

from django.utils import timezone

TIME_FORMAT = '%d-%m-%Y %H:%M'


def make_shopping_cart_file(
    ingredients: Iterable[dict], recipes: Iterable
) -> BytesIO:
    """
    Generate shopping cart text file content.

    Creates a formatted text document containing aggregated ingredients
    and recipe list from user's shopping cart.

    Args:
        ingredients: Iterable of ingredient dictionaries with keys:
                     ingredient__name, ingredient__measurement_unit, amount
        recipes: Iterable of Recipe instances

    Returns:
        BytesIO: Buffer containing formatted text document
    """
    current_time = timezone.now().strftime(TIME_FORMAT)

    # Format ingredients list
    ingredient_lines = [
        f'{index}. {item["ingredient__name"].capitalize()} '
        f'({item["ingredient__measurement_unit"]}) - '
        f'{item["amount"]}'
        for index, item in enumerate(ingredients, start=1)
    ]

    # Format recipes list
    recipe_lines = [
        f'{index}. {recipe.name}'
        for index, recipe in enumerate(recipes, start=1)
    ]

    # Combine all sections
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
