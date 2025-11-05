"""Admin configuration for accounts application."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.db.models import Count
from django.urls import reverse
from django.utils.safestring import mark_safe
from rest_framework.authtoken.models import TokenProxy

from .models import Account, FollowRelationship


admin.site.unregister(Group)
admin.site.unregister(TokenProxy)


class HasCulinaryItemsFilter(admin.SimpleListFilter):
    """Filter for accounts that have created culinary items."""
    title = 'Has Culinary Items'
    parameter_name = 'has_items'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Yes'),
            ('no', 'No'),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if not value:
            return queryset
        if value == 'yes':
            return queryset.filter(culinary_items_count__gt=0)
        return queryset.filter(culinary_items_count=0)


class HasFollowingFilter(admin.SimpleListFilter):
    """Filter for accounts that are following others."""
    title = 'Is Following'
    parameter_name = 'is_following'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Yes'),
            ('no', 'No'),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if not value:
            return queryset
        if value == 'yes':
            return queryset.filter(following_count__gt=0)
        return queryset.filter(following_count=0)


class HasFollowersFilter(admin.SimpleListFilter):
    """Filter for accounts that have followers."""
    title = 'Has Followers'
    parameter_name = 'has_followers'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Yes'),
            ('no', 'No'),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if not value:
            return queryset
        if value == 'yes':
            return queryset.filter(followers_count__gt=0)
        return queryset.filter(followers_count=0)


@admin.register(Account)
class AccountAdmin(BaseUserAdmin):
    """Admin interface for account management."""
    readonly_fields = (
        'followers_count',
        'following_count',
        'culinary_items_count',
    )
    list_display = (
        'id',
        'username',
        'email',
        'first_name',
        'last_name',
        'profile_picture_display',
        *readonly_fields,
    )
    list_filter = (
        HasCulinaryItemsFilter,
        HasFollowingFilter,
        HasFollowersFilter,
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('id',)

    def get_queryset(self, request):
        """Optimize queryset with annotations."""
        return (
            super()
            .get_queryset(request)
            .prefetch_related(
                'following_relationships',
                'follower_relationships',
                'culinary_items'
            )
            .annotate(
                followers_count=Count(
                    'follower_relationships', distinct=True
                ),
                following_count=Count(
                    'following_relationships', distinct=True
                ),
                culinary_items_count=Count(
                    'culinary_items', distinct=True
                ),
            )
        )

    @admin.display(description='Followers')
    def followers_count(self, account):
        """Display follower count."""
        return account.followers_count

    @admin.display(description='Following')
    def following_count(self, account):
        """Display following count."""
        return account.following_count

    @admin.display(description='Culinary Items')
    @mark_safe
    def culinary_items_count(self, account):
        """Display culinary items count with link."""
        if not account.culinary_items_count:
            return account.culinary_items_count
        url = reverse('admin:cookbook_culinaryitem_changelist')
        return (
            f"<a href='{url}?author__id__exact={account.id}'>"
            f'{account.culinary_items_count}</a>'
        )

    @admin.display(description='Profile Picture')
    @mark_safe
    def profile_picture_display(self, account):
        """Display profile picture thumbnail."""
        if not account.profile_picture:
            return '-'
        return (
            f"<img src='{account.profile_picture.url}' "
            "width='100' height='100' "
            "style='object-fit: cover;' />"
        )


@admin.register(FollowRelationship)
class FollowRelationshipAdmin(admin.ModelAdmin):
    """Admin interface for follow relationships."""
    list_display = ('follower', 'following', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('follower__username', 'following__username')
