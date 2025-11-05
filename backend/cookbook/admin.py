"""Admin configuration for cookbook application."""
from django import forms
from django.contrib import admin
from django.db.models import Count
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import (
    Bookmark,
    Category,
    Component,
    CulinaryItem,
    ItemComponent,
    WishlistItem,
)


class ItemComponentInline(admin.TabularInline):
    """Inline admin for item components."""
    model = ItemComponent
    extra = 1
    fields = ('component', 'quantity')


class ImageWidget(forms.ClearableFileInput):
    """Custom widget for image display in admin."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs['class'] = 'vTextField'

    @mark_safe
    def render(self, name, value, attrs=None, renderer=None):
        """Render image preview with upload field."""
        html = super().render(name, value, attrs, renderer)
        if value and hasattr(value, 'url'):
            html = (
                '<div>'
                f"<img src='{value.url}' "
                "width='200' height='200' /><br>"
                f'{html}'
                '</div>'
            )
        return html


class CulinaryItemForm(forms.ModelForm):
    """Form for culinary item admin."""
    class Meta:
        model = CulinaryItem
        fields = '__all__'
        widgets = {
            'image': ImageWidget,
        }


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin interface for categories."""
    list_display = ('id', 'name', 'slug', 'items_count')

    def get_queryset(self, request):
        """Optimize queryset with item count."""
        queryset = super().get_queryset(request)
        return queryset.annotate(
            items_count=Count('culinary_items', distinct=True)
        )

    @admin.display(description='Items')
    @mark_safe
    def items_count(self, category):
        """Display item count with link."""
        if not category.items_count:
            return category.items_count
        url = reverse('admin:cookbook_culinaryitem_changelist')
        return (
            f"<a href='{url}?categories__id__exact={category.id}'>"
            f'{category.items_count}</a>'
        )


@admin.register(Component)
class ComponentAdmin(admin.ModelAdmin):
    """Admin interface for components."""
    list_display = ('id', 'name', 'measurement_unit', 'items_count')
    list_filter = ('measurement_unit',)
    search_fields = ('name',)

    def get_queryset(self, request):
        """Optimize queryset with item count."""
        queryset = super().get_queryset(request)
        return queryset.annotate(
            items_count=Count('item_components__item', distinct=True)
        )

    @admin.display(description='Items')
    def items_count(self, component):
        """Display item count."""
        return component.items_count


@admin.register(CulinaryItem)
class CulinaryItemAdmin(admin.ModelAdmin):
    """Admin interface for culinary items."""
    form = CulinaryItemForm
    readonly_fields = ('bookmarks_count',)
    list_display = (
        'name',
        'author',
        'image_display',
        'description',
        'preparation_time',
        'bookmarks_count',
        'categories_list',
        'components_list',
    )
    list_filter = (
        'categories',
        ('author', admin.RelatedOnlyFieldListFilter),
    )
    search_fields = ('name', 'categories__name', 'components__name')
    inlines = (ItemComponentInline,)

    def get_queryset(self, request):
        """Optimize queryset with related objects."""
        return (
            super()
            .get_queryset(request)
            .select_related('author')
            .prefetch_related(
                'categories',
                'components',
                'item_components__component'
            )
            .annotate(bookmarks_count=Count('bookmark_relations'))
        )

    @admin.display(description='Bookmarks')
    def bookmarks_count(self, item):
        """Display bookmark count."""
        return item.bookmarks_count

    @admin.display(description='Image')
    @mark_safe
    def image_display(self, item):
        """Display image thumbnail."""
        if not item.image:
            return '-'
        return (
            f"<img src='{item.image.url}' width='100' height='100' "
            "style='object-fit: cover;' />"
        )

    @admin.display(description='Components')
    @mark_safe
    def components_list(self, item):
        """Display components list."""
        return '<br>'.join(
            f'{item_comp.component.name} '
            f'({item_comp.component.measurement_unit}) - '
            f'{item_comp.quantity}'
            for item_comp in item.item_components.select_related('component')
        )

    @admin.display(description='Categories')
    @mark_safe
    def categories_list(self, item):
        """Display categories list."""
        return '<br>'.join(category.name for category in item.categories.all())


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    """Admin interface for bookmarks."""
    list_display = ('account', 'item')
    list_filter = (
        ('account', admin.RelatedOnlyFieldListFilter),
        ('item', admin.RelatedOnlyFieldListFilter),
    )


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    """Admin interface for wishlist items."""
    list_display = ('account', 'item')
    list_filter = (
        ('account', admin.RelatedOnlyFieldListFilter),
        ('item', admin.RelatedOnlyFieldListFilter),
    )
