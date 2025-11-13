"""Валидаторы для API Foodgram."""

from __future__ import annotations

import re

from django.conf import settings
from django.core.exceptions import ValidationError


def validate_username(value: str) -> str:
    """Проверяет корректность имени пользователя."""
    allowed_pattern = settings.USERNAME_PATTERN

    # Извлекаем символы, не совпадающие с допустимым паттерном
    invalid_chars = re.sub(pattern=allowed_pattern, repl="", string=value)
    if invalid_chars:
        # Получаем уникальные недопустимые символы
        # для понятного сообщения об ошибке
        unique_invalid = "".join(sorted(set(invalid_chars)))
        raise ValidationError(
            f"Обнаружены недопустимые символы: {unique_invalid}"
        )

    # Проверяем против запрещенных имен пользователей
    forbidden_names = settings.FORBIDDEN_USERNAMES
    if value in forbidden_names:
        raise ValidationError(f'Имя пользователя "{value}" недопустимо!')

    return value
