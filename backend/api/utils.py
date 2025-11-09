from io import BytesIO

from django.utils import timezone

DATETIME_FORMAT = '%d-%m-%Y %H:%M'
ENCODING = 'utf-8'


def _format_ingredient_line(position, ingredient_data):
    """Форматирует строку с информацией об ингредиенте."""
    return (
        f'{position}. {ingredient_data["ingredient__name"].capitalize()} '
        f'({ingredient_data["ingredient__measurement_unit"]}) - '
        f'{ingredient_data["amount"]}'
    )


def _format_recipe_line(position, recipe_obj):
    """Форматирует строку с названием рецепта."""
    return f'{position}. {recipe_obj.name}'


def make_shopping_cart_file(ingredients_data, recipes_queryset):
    """Генерирует текстовый файл со списком покупок и рецептами."""

    timestamp = timezone.now().strftime(DATETIME_FORMAT)

    formatted_ingredients = [
        _format_ingredient_line(idx, ingredient)
        for idx, ingredient in enumerate(ingredients_data, start=1)
    ]

    formatted_recipes = [
        _format_recipe_line(idx, recipe)
        for idx, recipe in enumerate(recipes_queryset, start=1)
    ]

    document_lines = [
        f'Дата и время: {timestamp}',
        '',
        'Список покупок:',
        *formatted_ingredients,
        '',
        'Список рецептов:',
        *formatted_recipes,
    ]

    content_text = '\n'.join(document_lines)
    return BytesIO(content_text.encode(ENCODING))
