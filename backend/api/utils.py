from io import BytesIO
from django.utils import timezone


TIME_FORMAT = '%d-%m-%Y %H:%M'


def make_shopping_cart_file(ingredients, recipes):
    current_time = timezone.now().strftime(TIME_FORMAT)
    ingredients_list = [
        f'{index}. {item["ingredient__name"].capitalize()} '
        f'({item["ingredient__measurement_unit"]}) - '
        f'{item["amount"]}'
        for index, item in enumerate(ingredients, start=1)
    ]
    recipes_list = [
        f'{index}. {recipe.name}'
        for index, recipe in enumerate(recipes, start=1)
    ]
    content = '\n'.join(
        [
            f'Дата и время: {current_time}',
            '',
            'Список покупок:',
            *ingredients_list,
            '',
            'Список рецептов:',
            *recipes_list,
        ]
    )
    return BytesIO(content.encode('utf-8'))

