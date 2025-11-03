"""
Constants for recipes app.

This module contains all constant classes used across the recipes app
to avoid circular imports.
"""


class MinValue:
    """Minimum values for validation."""
    COOKING_TIME = 1
    AMOUNT = 1


class VerboseName:
    """Verbose names for model fields."""
    NAME = 'Название'
    SLUG = 'Идентификатор'
    TAG = 'Тег'
    MEASUREMENT_UNIT = 'Ед. измерения'
    INGREDIENT = 'Продукт'
    AUTHOR = 'Автор'
    IMAGE = 'Изображение'
    TEXT = 'Описание'
    COOKING_TIME = 'Время приготовления (в минутах)'
    PUB_DATE = 'Дата публикации'
    RECIPE = 'Рецепт'
    AMOUNT = 'Мера'
    FAVORITE = 'Избранное'
    SHOPPING_CART = 'Корзина покупок'
    EMAIL = 'Эл. почта'
    USERNAME = 'Уникальный юзернейм'
    FIRST_NAME = 'Имя'
    LAST_NAME = 'Фамилия'
    AVATAR = 'Фото профиля'
    SUBSCRIBER = 'Подписчик'
    SUBSCRIPTION = 'Подписка'
    USER = 'Пользователь'
    RECIPE_INGREDIENT = 'Продукт рецепта'
    SHORT_URL_CODE = 'Код рецепта'


class VerboseNamePlural:
    """Plural verbose names for model fields."""
    TAGS = 'Теги'
    INGREDIENTS = 'Продукты'
    RECIPES = 'Рецепты'
    FAVORITES = 'Избранные рецепты'
    SHOPPING_CARTS = 'Корзины покупок'
    SUBSCRIPTIONS = 'Подписки'
    USERS = 'Пользователи'
    RECIPE_INGREDIENTS = 'Продукты рецепта'
    SHORT_URL_CODE = 'Коды рецептов'


class FieldLength:
    """Field length constants for models."""
    TAG = 32
    INGREDIENT = 128
    MEASUREMENT_UNIT = 64
    RECIPE_NAME = 256
    EMAIL = 254
    USERNAME = 150
    FIRST_NAME = 150
    LAST_NAME = 150
    SHORT_URL_CODE = 6


class Error:
    """Error messages for validation and business logic."""
    COOKING_TIME = f'Не менее {MinValue.COOKING_TIME} мин. приготовления'
    AMOUNT = f'Не менее {MinValue.AMOUNT} ед. ингредиента'
    ALREADY_IN_SHOPPING_CART = 'Рецепт уже есть в списке покупок'
    ALREADY_FAVORITED = 'Рецепт уже есть в избранном'
    NOT_IN_SHOPPING_CART = 'Рецепта нет в списке покупок'
    NOT_FAVORITED = 'Рецепта нет в избранном'
    ALREADY_SUBSCRIBED = 'Вы уже подписаны на этого автора'
    CANNOT_SUBSCRIBE_TO_YOURSELF = 'Нельзя подписаться на самого себя'
    DUPLICATES = 'Дубликаты: {}'
    NO_IMAGE = 'Поле "image" не может быть пустым'
    NOT_SUBSCRIBED = 'Вы не подписаны на этого автора'
    NO_TAGS = 'Нужен хотя бы один тег'
    NO_INGREDIENTS = 'Рецепт не может обойтись без продуктов'
    NOT_EXIST = 'Рецепт не существует'
    SHORT_URL_CODE = 'Не удалось сгенерировать уникальный код'
    SHORT_URL_CODE_GEN = (
        'Превышено количество попыток генерации short_url_code.'
    )
