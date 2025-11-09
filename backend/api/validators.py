import re
from django.conf import settings
from django.core.exceptions import ValidationError


def validate_username(username):
    """Валидация имени пользователя."""
    pattern = settings.USERNAME_PATTERN
    forbidden_symbols = re.sub(pattern=pattern, repl='', string=username)
    if forbidden_symbols:
        forbidden_symbols = ''.join(set(forbidden_symbols))
        raise ValidationError(
            f'Обнаружены недопустимые символы: {forbidden_symbols}'
        )
    if username in settings.FORBIDDEN_USERNAMES:
        raise ValidationError(f'Имя пользователя "{username}" недопустимо!')
    return username
