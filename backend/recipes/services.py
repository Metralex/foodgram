"""
Бизнес-логика сервисов для приложения recipes.

Модуль содержит классы сервисов, которые инкапсулируют бизнес-логику,
отделённую от моделей и представлений.
"""
from random import choices
from string import ascii_letters, digits
from typing import TYPE_CHECKING

from .constants import Error, FieldLength

if TYPE_CHECKING:
    from .models import Recipe


class ShortUrlCodeGenerator:
    """Сервис для генерации уникальных кодов коротких ссылок для рецептов."""

    MAX_ATTEMPTS = 30
    AVAILABLE_CHARS = ascii_letters + digits
    CODE_LENGTH = FieldLength.SHORT_URL_CODE

    @classmethod
    def generate_code(cls) -> str:
        """
        Сгенерировать случайный код короткой ссылки.

        Возвращает:
            str: Случайный код из CODE_LENGTH символов.

        Вызывает:
            RuntimeError: Если не удаётся сгенерировать уникальный код.
        """
        # Импортируем здесь, чтобы избежать циклического импорта
        from .models import Recipe

        for _ in range(cls.MAX_ATTEMPTS):
            code = ''.join(choices(cls.AVAILABLE_CHARS, k=cls.CODE_LENGTH))
            if not Recipe.objects.filter(short_url_code=code).exists():
                return code
        raise RuntimeError(Error.SHORT_URL_CODE)

    @classmethod
    def ensure_unique_code(cls, recipe: 'Recipe') -> str:
        """
        Обеспечить наличие уникального кода короткой ссылки для рецепта.

        Генерирует уникальный код и назначает его экземпляру рецепта.
        Не сохраняет экземпляр - вызывающая функция должна обработать
        сохранение.

        Аргументы:
            recipe: Экземпляр рецепта для назначения кода.

        Возвращает:
            str: Уникальный код короткой ссылки.

        Вызывает:
            RuntimeError: Если не удаётся сгенерировать уникальный код.
        """
        # Импортируем здесь, чтобы избежать циклического импорта
        from .models import Recipe

        if recipe.short_url_code:
            return recipe.short_url_code

        attempts = 0
        while attempts < cls.MAX_ATTEMPTS:
            code = cls.generate_code()
            # Проверяем уникальность кода перед назначением
            if not Recipe.objects.filter(short_url_code=code).exists():
                recipe.short_url_code = code
                return code
            attempts += 1

        raise RuntimeError(Error.SHORT_URL_CODE_GEN)
