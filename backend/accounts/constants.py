"""Константы, используемые в приложении accounts."""


class FieldConstraints:
    """Ограничения длины полей и валидации."""
    EMAIL_MAX_LENGTH = 254
    USERNAME_MAX_LENGTH = 150
    FIRST_NAME_MAX_LENGTH = 150
    LAST_NAME_MAX_LENGTH = 150


class ValidationMessages:
    """Сообщения об ошибках для валидации."""
    RESERVED_USERNAME = 'The username "{}" is reserved and cannot be used.'
    INVALID_USERNAME_CHARS = 'Invalid characters detected: {}'


class DisplayNames:
    """Человекочитаемые имена полей для админки и форм."""
    EMAIL = 'Email Address'
    USERNAME = 'Username'
    FIRST_NAME = 'First Name'
    LAST_NAME = 'Last Name'
    PROFILE_PICTURE = 'Profile Picture'
    ACCOUNT = 'Account'
    ACCOUNTS = 'Accounts'
    FOLLOWER = 'Follower'
    FOLLOWING = 'Following'
    FOLLOW_RELATIONSHIP = 'Follow Relationship'
    FOLLOW_RELATIONSHIPS = 'Follow Relationships'
