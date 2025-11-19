"""Команда управления для импорта тегов из CSV файла."""

import csv
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandParser

from recipes.models import Tag


class Command(BaseCommand):

    """Импорт тегов из CSV файла в базу данных."""

    help = 'Import tags from CSV file located in data/recipes_tag.csv'

    def add_arguments(self, parser: CommandParser):
        """Добавляет аргументы командной строки."""
        parser.add_argument(
            '--file',
            type=str,
            default='data/recipes_tag.csv',
            help='Path to the CSV file (relative to BASE_DIR)',
        )

    def handle(self, *args: Any, **options: Any):
        """Выполняет логику команды."""
        csv_path = Path(settings.BASE_DIR) / options['file']

        if not csv_path.exists():
            self.stdout.write(self.style.ERROR(f'Файл не найден: {csv_path}'))
            return

        self.stdout.write(f'Импорт тегов из {csv_path}...')

        tags = []
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                tags.append(Tag(name=row['name'], slug=row['slug']))

        created_count = len(tags)
        Tag.objects.bulk_create(tags, ignore_conflicts=True)

        self.stdout.write(
            self.style.SUCCESS(f'Успешно импортировано {created_count} тегов')
        )
