"""Utility functions for gateway operations."""
from io import BytesIO
from typing import Iterable

from django.utils import timezone

DATE_TIME_FORMAT = '%d-%m-%Y %H:%M'


def generate_wishlist_file(
    components: Iterable[dict], items: Iterable
) -> BytesIO:
    """
    Generate a text file containing wishlist data.

    Creates a formatted text document with aggregated components
    and a list of culinary items from the user's wishlist.

    Args:
        components: Iterable of component dictionaries with keys:
            component__name, component__measurement_unit, quantity
        items: Iterable of CulinaryItem instances.

    Returns:
        BytesIO buffer containing the formatted text document.
    """
    timestamp = timezone.now().strftime(DATE_TIME_FORMAT)

    component_lines = [
        f'{idx}. {item["component__name"].capitalize()} '
        f'({item["component__measurement_unit"]}) - '
        f'{item["quantity"]}'
        for idx, item in enumerate(components, start=1)
    ]

    item_lines = [
        f'{idx}. {item.name}'
        for idx, item in enumerate(items, start=1)
    ]

    document_parts = [
        f'Generated: {timestamp}',
        '',
        'Component List:',
        *component_lines,
        '',
        'Culinary Items:',
        *item_lines,
    ]

    document_text = '\n'.join(document_parts)
    return BytesIO(document_text.encode('utf-8'))
