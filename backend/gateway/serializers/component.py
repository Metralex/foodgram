"""Serializers for component-related endpoints."""
from rest_framework import serializers

from cookbook.models import Component


class ComponentSerializer(serializers.ModelSerializer):
    """Serializer for component/ingredient data."""
    class Meta:
        model = Component
        fields = '__all__'
