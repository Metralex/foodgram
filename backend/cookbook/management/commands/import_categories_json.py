"""Management command to import categories from JSON file."""
import json

from django.core.management.base import BaseCommand

from cookbook.models import Category

PATH_JSON = 'data/recipes_tag.json'


class Command(BaseCommand):
    """Import category data from JSON file into the database."""
    help = 'Import categories from JSON file into the database'

    def handle(self, *args, **kwargs):
        """Execute the import operation."""
        with open(PATH_JSON, 'r', encoding='utf-8') as file:
            data = json.load(file)
            Category.objects.bulk_create(
                (Category(**tag) for tag in data),
                ignore_conflicts=True
            )
        self.stdout.write(
            self.style.SUCCESS('Categories imported successfully')
        )
