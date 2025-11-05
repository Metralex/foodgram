"""Management command to import categories from CSV file."""
import csv

from django.core.management.base import BaseCommand

from cookbook.models import Category

PATH_CSV = 'data/recipes_tag.csv'


class Command(BaseCommand):
    """Import category data from CSV file into the database."""
    help = 'Import categories from CSV file into the database'

    def handle(self, *args, **kwargs):
        """Execute the import operation."""
        with open(PATH_CSV, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            Category.objects.bulk_create(
                (Category(**tag) for tag in csv_reader),
                ignore_conflicts=True
            )
        self.stdout.write(
            self.style.SUCCESS('Categories imported successfully')
        )
