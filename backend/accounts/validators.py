"""Валидаторы для полей, связанных с аккаунтами."""
import re

from django.conf import settings
from django.core.exceptions import ValidationError

from .constants import ValidationMessages


def validate_account_username(value: str) -> str:
    """
    Проверяет, что имя пользователя содержит только разрешенные символы.

    Убеждается, что имя пользователя соответствует настроенному паттерну
    и не находится в списке зарезервированных имен.

    Args:
        value: Строка имени пользователя для валидации.

    Returns:
        Валидированное имя пользователя.

    Raises:
        ValidationError: Если имя пользователя содержит недопустимые символы
            или зарезервировано.
    """
    pattern = settings.USERNAME_PATTERN
    invalid_chars = re.sub(pattern=pattern, repl='', string=value)

    if invalid_chars:
        unique_invalid = ''.join(set(invalid_chars))
        raise ValidationError(
            ValidationMessages.INVALID_USERNAME_CHARS.format(unique_invalid)
        )

    reserved_names = settings.FORBIDDEN_USERNAMES
    if value in reserved_names:
        raise ValidationError(
            ValidationMessages.RESERVED_USERNAME.format(value)
        )

    return value
