"""Команда управления для импорта ингредиентов из CSV файла."""

import csv
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandParser
from recipes.models import Ingredient


class Command(BaseCommand):

    """Импорт ингредиентов из CSV файла в базу данных."""

    help = 'Import ingredients from CSV file located in data/ingredients.csv'

    def add_arguments(self, parser: CommandParser):
        """Добавляет аргументы командной строки."""
        parser.add_argument(
            '--file',
            type=str,
            default='data/ingredients.csv',
            help='Path to the CSV file (relative to BASE_DIR)',
        )

    def handle(self, *args: Any, **options: Any):
        """Выполняет логику команды."""
        csv_path = Path(settings.BASE_DIR) / options['file']

        if not csv_path.exists():
            self.stdout.write(self.style.ERROR(f'Файл не найден: {csv_path}'))
            return

        self.stdout.write(f'Импорт ингредиентов из {csv_path}...')

        ingredients = []
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                ingredients.append(
                    Ingredient(
                        name=row['name'],
                        measurement_unit=row['measurement_unit'],
                    )
                )

        created_count = len(ingredients)
        Ingredient.objects.bulk_create(ingredients, ignore_conflicts=True)

        self.stdout.write(
            self.style.SUCCESS(
                f'Успешно импортировано {created_count} ингредиентов'
            )
        )
