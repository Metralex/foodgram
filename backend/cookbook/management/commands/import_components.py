"""Management command to import components from CSV file."""
import csv

from django.core.management.base import BaseCommand

from cookbook.models import Component

PATH_CSV = 'data/ingredients.csv'


class Command(BaseCommand):
    """Import component data from CSV file into the database."""
    help = 'Import components from CSV file into the database'

    def handle(self, *args, **kwargs):
        """Execute the import operation."""
        with open(PATH_CSV, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            Component.objects.bulk_create(
                (Component(**row) for row in csv_reader),
                ignore_conflicts=True,
            )
        self.stdout.write(
            self.style.SUCCESS('Components imported successfully')
        )
