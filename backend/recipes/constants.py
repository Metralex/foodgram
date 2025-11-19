"""Константы для приложения recipes."""

from string import ascii_letters, digits


TAG_SLUG_MAX_LENGTH = 200
CHAR_MAX_LENGTH = 200


SHORT_CODE_LENGTH = 6
SHORT_CODE_ALPHABET = ascii_letters + digits
SHORT_CODE_GENERATION_MAX_ATTEMPTS = 30


RECIPE_COOKING_MINIMUM = 1
RECIPE_COOKING_ERROR = 'Минимум 1 минута'
INGREDIENT_AMOUNT_MINIMUM = 1
INGREDIENT_AMOUNT_ERROR = 'Минимум 1'
