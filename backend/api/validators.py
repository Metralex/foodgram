"""Валидаторы для API Foodgram."""

from __future__ import annotations

import re

from django.conf import settings
from django.core.exceptions import ValidationError


def validate_username(value: str) -> str:
    """Проверяет корректность имени пользователя."""
    allowed_pattern = settings.USERNAME_PATTERN

    # Extract any characters that don't match the allowed pattern
    invalid_chars = re.sub(pattern=allowed_pattern, repl="", string=value)
    if invalid_chars:
        # Get unique invalid characters for a clearer error message
        unique_invalid = "".join(sorted(set(invalid_chars)))
        raise ValidationError(
            f"Обнаружены недопустимые символы: {unique_invalid}"
        )

    # Check against forbidden usernames
    forbidden_names = settings.FORBIDDEN_USERNAMES
    if value in forbidden_names:
        raise ValidationError(f'Имя пользователя "{value}" недопустимо!')

    return value
