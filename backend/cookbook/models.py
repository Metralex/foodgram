"""Models for culinary content management."""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import IntegrityError, models
from django.db.models.constraints import UniqueConstraint

from .constants import (
    DisplayNames,
    FieldConstraints,
    MinimumValues,
    ValidationMessages,
)
from .generators import ShortLinkGenerator

Account = get_user_model()


class Category(models.Model):
    """
    Represents a categorization tag for culinary items.

    Categories enable filtering and organization of culinary
    content by type, cuisine, dietary restrictions, etc.
    """
    name = models.CharField(
        verbose_name=DisplayNames.NAME,
        max_length=FieldConstraints.CATEGORY_NAME_MAX,
        unique=True,
        help_text='Unique name for the category.'
    )
    slug = models.SlugField(
        verbose_name=DisplayNames.SLUG,
        max_length=FieldConstraints.CATEGORY_NAME_MAX,
        unique=True,
        help_text='URL-friendly identifier for the category.'
    )

    class Meta:
        verbose_name = DisplayNames.CATEGORY
        verbose_name_plural = DisplayNames.CATEGORIES
        default_related_name = 'categories'
        ordering = ('name',)
        db_table = 'cookbook_category'

    def __str__(self) -> str:
        """Return the category name."""
        return self.name


class Component(models.Model):
    """
    Represents an ingredient or component used in culinary items.

    Stores both the component name and its standard measurement unit,
    enabling consistent quantity tracking across recipes.
    """
    name = models.CharField(
        verbose_name=DisplayNames.NAME,
        max_length=FieldConstraints.COMPONENT_NAME_MAX,
        help_text='Name of the component or ingredient.'
    )
    measurement_unit = models.CharField(
        verbose_name=DisplayNames.MEASUREMENT_UNIT,
        max_length=FieldConstraints.UNIT_NAME_MAX,
        help_text='Standard unit of measurement for this component.'
    )

    class Meta:
        verbose_name = DisplayNames.COMPONENT
        verbose_name_plural = DisplayNames.COMPONENTS
        default_related_name = 'components'
        ordering = ('name',)
        db_table = 'cookbook_component'

    def __str__(self) -> str:
        """Return name and unit in a readable format."""
        return f'{self.name} ({self.measurement_unit})'


class CulinaryItem(models.Model):
    """
    Represents a complete culinary recipe or cooking instruction set.

    Combines ingredients, preparation steps, timing, and metadata
    into a shareable culinary content item. Includes automatic
    short link generation for easy sharing.
    """
    name = models.CharField(
        verbose_name=DisplayNames.NAME,
        max_length=FieldConstraints.CULINARY_ITEM_NAME_MAX,
        help_text='Title of the culinary item.'
    )
    categories = models.ManyToManyField(
        to=Category,
        verbose_name=DisplayNames.CATEGORIES,
        related_name='culinary_items',
        help_text='Categories this item belongs to.'
    )
    components = models.ManyToManyField(
        to=Component,
        through='ItemComponent',
        verbose_name=DisplayNames.COMPONENTS,
        related_name='culinary_items',
        help_text='Components or ingredients required for this item.'
    )
    author = models.ForeignKey(
        to=Account,
        on_delete=models.CASCADE,
        verbose_name=DisplayNames.AUTHOR,
        related_name='culinary_items',
        help_text='Account that created this item.'
    )
    image = models.ImageField(
        verbose_name=DisplayNames.IMAGE,
        upload_to=settings.RECIPES_IMAGES_PATH,
        help_text='Primary image for the culinary item.'
    )
    description = models.TextField(
        verbose_name=DisplayNames.DESCRIPTION,
        help_text='Detailed description and preparation instructions.'
    )
    preparation_time = models.PositiveIntegerField(
        verbose_name=DisplayNames.PREPARATION_TIME,
        validators=[
            MinValueValidator(
                limit_value=MinimumValues.PREPARATION_TIME_MIN,
                message=ValidationMessages.PREP_TIME_TOO_SHORT,
            )
        ],
        help_text='Time required for preparation in minutes.'
    )
    short_code = models.SlugField(
        verbose_name=DisplayNames.SHORT_CODE,
        max_length=FieldConstraints.SHORT_CODE_LENGTH,
        unique=True,
        help_text='Short code for generating shareable links.'
    )
    published_at = models.DateTimeField(
        verbose_name=DisplayNames.PUBLICATION_DATE,
        auto_now_add=True,
        help_text='Timestamp when the item was published.'
    )

    class Meta:
        verbose_name = DisplayNames.CULINARY_ITEM
        verbose_name_plural = DisplayNames.CULINARY_ITEMS
        default_related_name = 'culinary_items'
        ordering = ('-published_at',)
        db_table = 'cookbook_culinaryitem'

    def __str__(self) -> str:
        """Return the item name."""
        return self.name

    def save(self, *args, **kwargs):
        """
        Save the instance with automatic short code generation.

        Handles code generation and uniqueness conflicts with
        retry logic to ensure successful persistence.
        """
        if not self.short_code:
            ShortLinkGenerator.assign_unique_code(self)

        attempts = 0
        while attempts < ShortLinkGenerator.MAX_RETRIES:
            try:
                super().save(*args, **kwargs)
                break
            except IntegrityError as err:
                if 'short_code' in str(err):
                    attempts += 1
                    if attempts >= ShortLinkGenerator.MAX_RETRIES:
                        raise RuntimeError(
                            ValidationMessages.SHORT_CODE_MAX_ATTEMPTS
                        )
                    self.short_code = ShortLinkGenerator.generate()
                else:
                    raise


class ItemComponent(models.Model):
    """
    Junction model linking culinary items to components with quantities.

    Represents the many-to-many relationship between items and components,
    storing the required quantity of each component per item.
    """
    item = models.ForeignKey(
        to=CulinaryItem,
        on_delete=models.CASCADE,
        verbose_name=DisplayNames.CULINARY_ITEM,
        related_name='item_components',
        help_text='The culinary item this component belongs to.'
    )
    component = models.ForeignKey(
        to=Component,
        on_delete=models.CASCADE,
        verbose_name=DisplayNames.COMPONENT,
        related_name='item_components',
        help_text='The component being used.'
    )
    quantity = models.PositiveIntegerField(
        verbose_name=DisplayNames.QUANTITY,
        validators=[
            MinValueValidator(
                limit_value=MinimumValues.QUANTITY_MIN,
                message=ValidationMessages.QUANTITY_TOO_LOW,
            )
        ],
        help_text='Required quantity of this component.'
    )

    class Meta:
        default_related_name = 'item_components'
        ordering = ('item', 'component')
        constraints = (
            UniqueConstraint(
                fields=('item', 'component'),
                name='unique_item_component'
            ),
        )
        verbose_name = DisplayNames.ITEM_COMPONENT
        verbose_name_plural = DisplayNames.ITEM_COMPONENTS
        db_table = 'cookbook_itemcomponent'

    def __str__(self) -> str:
        """Return a human-readable representation."""
        return f'{self.component.name} for {self.item.name}'


class BaseUserItemRelation(models.Model):
    """
    Abstract base model for user-item relationships.

    Provides common structure for bookmark and wishlist models,
    ensuring consistent foreign key relationships and constraints.
    """
    account = models.ForeignKey(
        to=Account,
        on_delete=models.CASCADE,
        verbose_name='Account',
        help_text='The account that owns this relationship.'
    )
    item = models.ForeignKey(
        to=CulinaryItem,
        on_delete=models.CASCADE,
        verbose_name=DisplayNames.CULINARY_ITEM,
        help_text='The culinary item in this relationship.'
    )

    class Meta:
        abstract = True
        ordering = ('item',)
        default_related_name = '%(class)s_relations'

    def __str__(self) -> str:
        """Return a basic string representation."""
        return f'{self.account} - {self.item}'


class Bookmark(BaseUserItemRelation):
    """
    Represents a user's bookmark of a culinary item.

    Allows accounts to save items for later reference without
    adding them to a shopping list.
    """
    class Meta(BaseUserItemRelation.Meta):
        verbose_name = DisplayNames.BOOKMARK
        verbose_name_plural = DisplayNames.BOOKMARKS
        constraints = [
            models.UniqueConstraint(
                fields=['account', 'item'],
                name='unique_bookmark',
            ),
        ]
        db_table = 'cookbook_bookmark'


class WishlistItem(BaseUserItemRelation):
    """
    Represents a user's wishlist entry for a culinary item.

    Tracks items that users intend to prepare, enabling shopping
    list generation and meal planning features.
    """
    class Meta(BaseUserItemRelation.Meta):
        verbose_name = DisplayNames.WISHLIST_ITEM
        verbose_name_plural = DisplayNames.WISHLIST_ITEMS
        constraints = [
            models.UniqueConstraint(
                fields=['account', 'item'],
                name='unique_wishlist_item',
            ),
        ]
        db_table = 'cookbook_wishlistitem'
