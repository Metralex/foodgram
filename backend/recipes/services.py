"""
Business logic services for recipes app.

This module contains service classes that encapsulate business logic
separated from models and views for better maintainability.
"""
from random import choices
from string import ascii_letters, digits

from .models import Error, FieldLength, Recipe


class ShortUrlCodeGenerator:
    """Service for generating unique short URL codes for recipes."""

    MAX_ATTEMPTS = 30
    AVAILABLE_CHARS = ascii_letters + digits
    CODE_LENGTH = FieldLength.SHORT_URL_CODE

    @classmethod
    def generate_code(cls) -> str:
        """
        Generate a random short URL code.

        Returns:
            str: A random code of CODE_LENGTH characters.

        Raises:
            RuntimeError: If unable to generate unique code after MAX_ATTEMPTS.
        """
        for _ in range(cls.MAX_ATTEMPTS):
            code = ''.join(choices(cls.AVAILABLE_CHARS, k=cls.CODE_LENGTH))
            if not Recipe.objects.filter(short_url_code=code).exists():
                return code
        raise RuntimeError(Error.SHORT_URL_CODE)

    @classmethod
    def ensure_unique_code(cls, recipe: Recipe) -> str:
        """
        Ensure recipe has a unique short URL code.

        Generates a unique code and assigns it to recipe instance.
        Does not save the instance - caller should handle saving.

        Args:
            recipe: Recipe instance to assign code to.

        Returns:
            str: The unique short URL code.

        Raises:
            RuntimeError: If unable to generate unique code after MAX_ATTEMPTS.
        """
        if recipe.short_url_code:
            return recipe.short_url_code

        attempts = 0
        while attempts < cls.MAX_ATTEMPTS:
            code = cls.generate_code()
            # Check if code is unique before assigning
            if not Recipe.objects.filter(short_url_code=code).exists():
                recipe.short_url_code = code
                return code
            attempts += 1

        raise RuntimeError(Error.SHORT_URL_CODE_GEN)
