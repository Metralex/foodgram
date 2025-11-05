"""Serializers for account-related endpoints."""
from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer as DjoserUserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from accounts.models import FollowRelationship

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser

Account = get_user_model()


class AccountSerializer(DjoserUserSerializer):
    """
    Serializer for account data with follow status.

    Extends Djoser's user serializer to include profile picture
    and follow relationship status.
    """
    is_following = serializers.SerializerMethodField()

    class Meta:
        model = Account
        fields = (
            *DjoserUserSerializer.Meta.fields,
            'profile_picture',
            'is_following'
        )

    def get_is_following(self, account: 'AbstractUser') -> bool:
        """
        Check if the current user is following this account.

        Args:
            account: The account to check follow status for.

        Returns:
            True if the request user is following, False otherwise.
        """
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False

        return FollowRelationship.objects.filter(
            follower=request.user,
            following=account
        ).exists()


class ProfilePictureSerializer(serializers.ModelSerializer):
    """Serializer for profile picture upload/update."""
    profile_picture = Base64ImageField()

    class Meta:
        model = Account
        fields = ('profile_picture',)
