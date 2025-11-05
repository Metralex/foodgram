"""Constants used within the cookbook application."""


class FieldConstraints:
    """Field length and validation constraints."""
    CATEGORY_NAME_MAX = 32
    COMPONENT_NAME_MAX = 128
    UNIT_NAME_MAX = 64
    CULINARY_ITEM_NAME_MAX = 256
    SHORT_CODE_LENGTH = 6


class MinimumValues:
    """Minimum values for numeric validations."""
    PREPARATION_TIME_MIN = 1
    QUANTITY_MIN = 1


class ValidationMessages:
    """Error messages for validation."""
    PREP_TIME_TOO_SHORT = (
        f'Preparation time must be at least '
        f'{MinimumValues.PREPARATION_TIME_MIN} minute.'
    )
    QUANTITY_TOO_LOW = (
        f'Quantity must be at least '
        f'{MinimumValues.QUANTITY_MIN} unit.'
    )
    ALREADY_BOOKMARKED = 'This item is already bookmarked.'
    ALREADY_IN_WISHLIST = 'This item is already in your wishlist.'
    NOT_BOOKMARKED = 'This item is not bookmarked.'
    NOT_IN_WISHLIST = 'This item is not in your wishlist.'
    DUPLICATE_ENTRIES = 'Duplicate entries found: {}'
    IMAGE_REQUIRED = 'Image field cannot be empty.'
    SHORT_CODE_GENERATION_FAILED = 'Failed to generate unique short code.'
    SHORT_CODE_MAX_ATTEMPTS = (
        'Maximum attempts exceeded while generating short code.'
    )


class DisplayNames:
    """Human-readable field names for admin and forms."""
    NAME = 'Name'
    SLUG = 'Slug'
    CATEGORY = 'Category'
    CATEGORIES = 'Categories'
    MEASUREMENT_UNIT = 'Measurement Unit'
    COMPONENT = 'Component'
    COMPONENTS = 'Components'
    CULINARY_ITEM = 'Culinary Item'
    CULINARY_ITEMS = 'Culinary Items'
    AUTHOR = 'Author'
    IMAGE = 'Image'
    DESCRIPTION = 'Description'
    PREPARATION_TIME = 'Preparation Time (minutes)'
    PUBLICATION_DATE = 'Publication Date'
    QUANTITY = 'Quantity'
    BOOKMARK = 'Bookmark'
    BOOKMARKS = 'Bookmarks'
    WISHLIST_ITEM = 'Wishlist Item'
    WISHLIST_ITEMS = 'Wishlist Items'
    SHORT_CODE = 'Short Link Code'
    ITEM_COMPONENT = 'Item Component'
    ITEM_COMPONENTS = 'Item Components'
