import re

from django.conf import settings
from django.core.exceptions import ValidationError


def validate_username(value):
    """Проверяет корректность имени пользователя согласно правилам системы."""
    allowed_pattern = settings.USERNAME_PATTERN

    invalid_chars = re.sub(pattern=allowed_pattern, repl='', string=value)
    if invalid_chars:
        unique_invalid = ''.join(sorted(set(invalid_chars)))
        raise ValidationError(
            f'Обнаружены недопустимые символы: {unique_invalid}'
        )

    forbidden_names = settings.FORBIDDEN_USERNAMES
    if value in forbidden_names:
        raise ValidationError(f'Имя пользователя "{value}" недопустимо!')

    return value
