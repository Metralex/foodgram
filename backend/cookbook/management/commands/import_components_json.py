"""Management command to import components from JSON file."""
import json

from django.core.management.base import BaseCommand

from cookbook.models import Component

PATH_JSON = 'data/ingredients.json'


class Command(BaseCommand):
    """Import component data from JSON file into the database."""
    help = 'Import components from JSON file into the database'

    def handle(self, *args, **kwargs):
        """Execute the import operation."""
        with open(PATH_JSON, 'r', encoding='utf-8') as file:
            data = json.load(file)
            Component.objects.bulk_create(
                (Component(**component) for component in data),
                ignore_conflicts=True,
            )
        self.stdout.write(
            self.style.SUCCESS('Components imported successfully')
        )
