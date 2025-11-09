import csv
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from api.models import Ingredient


class Command(BaseCommand):
    help = 'Import ingredients from CSV file'

    def handle(self, *args, **options):
        csv_path = os.path.join(settings.BASE_DIR, 'data', 'ingredients.csv')
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            ingredients = []
            for row in reader:
                ingredients.append(
                    Ingredient(
                        name=row['name'],
                        measurement_unit=row['measurement_unit']
                    )
                )
            Ingredient.objects.bulk_create(ingredients, ignore_conflicts=True)
        self.stdout.write(
            self.style.SUCCESS('Ингредиенты успешно импортированы')
        )
