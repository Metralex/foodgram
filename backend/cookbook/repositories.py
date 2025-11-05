"""Repository pattern implementation for cookbook business logic."""
from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from rest_framework.exceptions import ValidationError

from .constants import ValidationMessages
from .models import Bookmark, CulinaryItem, WishlistItem

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser

Account = get_user_model()


class BookmarkRepository:
    """Repository for managing bookmark operations."""

    @staticmethod
    def create(account: 'AbstractUser', item: CulinaryItem) -> Bookmark:
        """
        Create a bookmark relationship between an account and item.

        Args:
            account: The account creating the bookmark.
            item: The culinary item to bookmark.

        Returns:
            The created Bookmark instance.

        Raises:
            ValidationError: If the bookmark already exists.
        """
        bookmark, created = Bookmark.objects.get_or_create(
            account=account, item=item
        )
        if not created:
            raise ValidationError(
                {'error': ValidationMessages.ALREADY_BOOKMARKED}
            )
        return bookmark

    @staticmethod
    def delete(account: 'AbstractUser', item: CulinaryItem) -> None:
        """
        Remove a bookmark relationship.

        Args:
            account: The account removing the bookmark.
            item: The culinary item to unbookmark.

        Raises:
            Http404: If the bookmark doesn't exist.
        """
        from django.shortcuts import get_object_or_404
        get_object_or_404(Bookmark, account=account, item=item).delete()

    @staticmethod
    def is_bookmarked(account: 'AbstractUser', item: CulinaryItem) -> bool:
        """
        Check if an item is bookmarked by an account.

        Args:
            account: The account to check.
            item: The culinary item to check.

        Returns:
            True if bookmarked, False otherwise.
        """
        if not account.is_authenticated:
            return False
        return Bookmark.objects.filter(account=account, item=item).exists()


class WishlistRepository:
    """Repository for managing wishlist operations."""

    @staticmethod
    def create(account: 'AbstractUser', item: CulinaryItem) -> WishlistItem:
        """
        Create a wishlist entry for an account and item.

        Args:
            account: The account adding to wishlist.
            item: The culinary item to add.

        Returns:
            The created WishlistItem instance.

        Raises:
            ValidationError: If the item is already in wishlist.
        """
        wishlist_item, created = WishlistItem.objects.get_or_create(
            account=account, item=item
        )
        if not created:
            raise ValidationError(
                {'error': ValidationMessages.ALREADY_IN_WISHLIST}
            )
        return wishlist_item

    @staticmethod
    def delete(account: 'AbstractUser', item: CulinaryItem) -> None:
        """
        Remove a wishlist entry.

        Args:
            account: The account removing from wishlist.
            item: The culinary item to remove.

        Raises:
            Http404: If the wishlist entry doesn't exist.
        """
        from django.shortcuts import get_object_or_404
        get_object_or_404(WishlistItem, account=account, item=item).delete()

    @staticmethod
    def is_in_wishlist(account: 'AbstractUser', item: CulinaryItem) -> bool:
        """
        Check if an item is in an account's wishlist.

        Args:
            account: The account to check.
            item: The culinary item to check.

        Returns:
            True if in wishlist, False otherwise.
        """
        if not account.is_authenticated:
            return False
        return WishlistItem.objects.filter(account=account, item=item).exists()


class CulinaryItemRepository:
    """Repository for culinary item queries and operations."""

    @staticmethod
    def get_optimized_queryset(account: 'AbstractUser' = None) -> QuerySet:
        """
        Get an optimized queryset with prefetched relations.

        Args:
            account: Optional account for user-specific prefetching.

        Returns:
            Optimized QuerySet with related objects prefetched.
        """
        queryset = (
            CulinaryItem.objects
            .select_related('author')
            .prefetch_related(
                'categories',
                'components',
                'item_components__component'
            )
        )

        if account and account.is_authenticated:
            from django.db.models import Prefetch
            queryset = queryset.prefetch_related(
                Prefetch(
                    'bookmark_relations',
                    queryset=Bookmark.objects.filter(account=account),
                    to_attr='_user_bookmarks'
                ),
                Prefetch(
                    'wishlistitem_relations',
                    queryset=WishlistItem.objects.filter(account=account),
                    to_attr='_user_wishlist_items'
                )
            )

        return queryset
