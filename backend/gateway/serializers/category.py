"""Serializers for category-related endpoints."""
from rest_framework import serializers

from cookbook.models import Category


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for category data."""
    class Meta:
        model = Category
        fields = '__all__'
