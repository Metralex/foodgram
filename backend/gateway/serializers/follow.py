"""Serializers for follow relationship endpoints."""
from typing import TYPE_CHECKING

from rest_framework import serializers

from .account import AccountSerializer

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser


class FollowRelationshipSerializer(AccountSerializer):
    """
    Serializer for follow relationship data.

    Extends account serializer to include followed account's
    culinary items with optional limit.
    """
    culinary_items = serializers.SerializerMethodField()
    culinary_items_count = serializers.SerializerMethodField()

    class Meta(AccountSerializer.Meta):
        fields = (
            *AccountSerializer.Meta.fields,
            'culinary_items',
            'culinary_items_count'
        )

    def get_culinary_items(self, account: 'AbstractUser') -> list:
        """
        Get culinary items for the followed account.

        Args:
            account: The account to get items for.

        Returns:
            List of serialized culinary items.
        """
        from .culinary_item import CulinaryItemSummarySerializer

        request = self.context.get('request')
        limit = int(request.GET.get('recipes_limit', 10**10))

        items = account.culinary_items.all()[:limit]
        return CulinaryItemSummarySerializer(
            items,
            context=self.context,
            many=True,
        ).data

    def get_culinary_items_count(self, account: 'AbstractUser') -> int:
        """Get total count of culinary items for the account."""
        return account.culinary_items.count()
