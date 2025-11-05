"""Code generation utilities for cookbook entities."""
from random import choices
from string import ascii_letters, digits
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import CulinaryItem


class ShortLinkGenerator:
    """
    Generates unique short codes for culinary items.

    Provides collision-resistant code generation with configurable
    retry logic for ensuring uniqueness.
    """
    MAX_RETRIES = 30
    CHARACTER_SET = ascii_letters + digits
    CODE_LENGTH = 6

    @classmethod
    def generate(cls) -> str:
        """
        Generate a random short code.

        Returns:
            A randomly generated alphanumeric code.

        Raises:
            RuntimeError: If unable to generate a unique code
                after maximum retries.
        """
        from .models import CulinaryItem

        for _ in range(cls.MAX_RETRIES):
            code = ''.join(choices(cls.CHARACTER_SET, k=cls.CODE_LENGTH))
            exists = CulinaryItem.objects.filter(short_code=code).exists()
            if not exists:
                return code

        raise RuntimeError('Failed to generate unique short code.')

    @classmethod
    def assign_unique_code(cls, item: 'CulinaryItem') -> str:
        """
        Assign a unique short code to a culinary item instance.

        Generates and assigns a unique code if one doesn't exist.
        The instance is not saved by this method.

        Args:
            item: The culinary item instance to assign a code to.

        Returns:
            The assigned short code.

        Raises:
            RuntimeError: If unable to generate a unique code.
        """
        from .models import CulinaryItem

        if item.short_code:
            return item.short_code

        for attempt in range(cls.MAX_RETRIES):
            code = cls.generate()
            exists = CulinaryItem.objects.filter(short_code=code).exists()
            if not exists:
                item.short_code = code
                return code

        raise RuntimeError(
            'Maximum attempts exceeded while generating short code.'
        )
