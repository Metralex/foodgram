"""Serializers for culinary item endpoints."""
from collections import Counter

from django.core.validators import MinValueValidator
from django.db import transaction
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from cookbook.constants import (
    MinimumValues,
    ValidationMessages,
)
from cookbook.models import Category, Component, CulinaryItem, ItemComponent
from cookbook.repositories import (
    BookmarkRepository,
    WishlistRepository,
)


class ItemComponentSerializer(serializers.ModelSerializer):
    """Serializer for item-component relationships with quantities."""
    id = serializers.PrimaryKeyRelatedField(
        queryset=Component.objects.all(),
        source='component'
    )
    name = serializers.ReadOnlyField(source='component.name')
    measurement_unit = serializers.ReadOnlyField(
        source='component.measurement_unit',
    )
    quantity = serializers.IntegerField(
        validators=[
            MinValueValidator(
                limit_value=MinimumValues.QUANTITY_MIN,
                message=ValidationMessages.QUANTITY_TOO_LOW
            )
        ]
    )

    class Meta:
        model = ItemComponent
        fields = ('id', 'name', 'measurement_unit', 'quantity')


class CulinaryItemSummarySerializer(serializers.ModelSerializer):
    """
    Compact serializer for culinary items in nested contexts.

    Used in follow relationship listings and other places where
    full item details are not required.
    """
    class Meta:
        model = CulinaryItem
        fields = (
            'id',
            'name',
            'image',
            'preparation_time',
        )


class CulinaryItemReadSerializer(serializers.ModelSerializer):
    """
    Serializer for reading culinary item data with full details.

    Includes categories, author, components, and user interaction
    flags for bookmark and wishlist status.
    """
    categories = serializers.SerializerMethodField()
    author = serializers.SerializerMethodField()
    components = serializers.SerializerMethodField()
    is_bookmarked = serializers.SerializerMethodField()
    is_in_wishlist = serializers.SerializerMethodField()

    class Meta:
        model = CulinaryItem
        fields = (
            'id',
            'categories',
            'author',
            'components',
            'name',
            'image',
            'description',
            'preparation_time',
            'is_bookmarked',
            'is_in_wishlist',
        )
        read_only_fields = fields

    def get_categories(self, obj: 'CulinaryItem'):
        """Get serialized categories."""
        from .category import CategorySerializer
        return CategorySerializer(obj.categories.all(), many=True).data

    def get_author(self, obj: 'CulinaryItem'):
        """Get serialized author."""
        from .account import AccountSerializer
        return AccountSerializer(obj.author, context=self.context).data

    def get_components(self, obj: 'CulinaryItem'):
        """Get serialized components with quantities."""
        return ItemComponentSerializer(
            obj.item_components.all(),
            many=True
        ).data

    def get_is_bookmarked(self, obj: 'CulinaryItem') -> bool:
        """Check if item is bookmarked by current user."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False

        if hasattr(obj, '_user_bookmarks'):
            return len(obj._user_bookmarks) > 0

        return BookmarkRepository.is_bookmarked(request.user, obj)

    def get_is_in_wishlist(self, obj: 'CulinaryItem') -> bool:
        """Check if item is in current user's wishlist."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False

        if hasattr(obj, '_user_wishlist_items'):
            return len(obj._user_wishlist_items) > 0

        return WishlistRepository.is_in_wishlist(request.user, obj)


class CulinaryItemWriteSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating culinary items.

    Handles nested component relationships and validates for
    duplicates and required fields.
    """
    components = serializers.ListField(
        child=ItemComponentSerializer(),
        allow_empty=False,
        required=True,
    )
    categories = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(
            queryset=Category.objects.all(),
        ),
        allow_empty=False,
        required=True,
    )
    image = Base64ImageField(allow_empty_file=False, required=True)

    class Meta:
        model = CulinaryItem
        fields = (
            'components',
            'categories',
            'image',
            'name',
            'description',
            'preparation_time',
        )

    @staticmethod
    def _validate_no_duplicates(items: list, field_name: str) -> None:
        """
        Validate that a list contains no duplicate values.

        Args:
            items: List of items to check.
            field_name: Name of the field for error messages.

        Raises:
            ValidationError: If duplicates are found.
        """
        counts = Counter(items)
        duplicates = {item for item, count in counts.items() if count > 1}
        if duplicates:
            raise serializers.ValidationError(
                {
                    field_name: ValidationMessages.DUPLICATE_ENTRIES.format(
                        duplicates
                    )
                }
            )

    def validate_categories(self, categories: list) -> list:
        """Validate category list for duplicates."""
        self._validate_no_duplicates(
            [cat.id for cat in categories], 'categories'
        )
        return categories

    def validate_components(self, components: list) -> list:
        """Validate component list for duplicates."""
        component_ids = [
            comp['component'].id if isinstance(comp, dict)
            else comp.id for comp in components
        ]
        self._validate_no_duplicates(component_ids, 'components')
        return components

    def validate_image(self, image) -> object:
        """Validate that image is provided."""
        if not image:
            raise serializers.ValidationError(
                ValidationMessages.IMAGE_REQUIRED
            )
        return image

    @staticmethod
    def _save_components(item: 'CulinaryItem', components_data: list) -> None:
        """
        Save component relationships using bulk operations.

        Args:
            item: The culinary item instance.
            components_data: List of component dictionaries with
                'component' and 'quantity' keys.
        """
        ItemComponent.objects.bulk_create(
            ItemComponent(
                item=item,
                component=comp['component'],
                quantity=comp['quantity'],
            )
            for comp in components_data
        )

    @transaction.atomic
    def create(self, validated_data: dict) -> 'CulinaryItem':
        """
        Create a new culinary item with components and categories.

        Args:
            validated_data: Validated serializer data.

        Returns:
            Created CulinaryItem instance.
        """
        components_data = validated_data.pop('components')
        categories_data = validated_data.pop('categories')
        item = super().create(validated_data)
        item.categories.set(categories_data)
        self._save_components(item, components_data)
        return item

    @transaction.atomic
    def update(
        self, item: 'CulinaryItem', validated_data: dict
    ) -> 'CulinaryItem':
        """
        Update an existing culinary item.

        Args:
            item: The item instance to update.
            validated_data: Validated serializer data.

        Returns:
            Updated CulinaryItem instance.
        """
        if 'components' in validated_data:
            components_data = validated_data.pop('components')
            item.components.clear()
            self._save_components(item, components_data)

        if 'categories' in validated_data:
            categories_data = validated_data.pop('categories')
            item.categories.set(categories_data)

        return super().update(item, validated_data)

    def to_representation(self, item: 'CulinaryItem') -> dict:
        """Convert to read serializer representation."""
        return CulinaryItemReadSerializer(
            item,
            context=self.context
        ).data
