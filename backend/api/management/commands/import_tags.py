import csv
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils.text import slugify
from api.models import Tag


class Command(BaseCommand):
    """Команда для импорта тегов из CSV файла."""

    help = 'Import tags from CSV file'

    def handle(self, *args, **options):
        csv_path = os.path.join(settings.BASE_DIR, 'data', 'recipes_tag.csv')
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            tags = []
            for row in reader:
                tags.append(
                    Tag(
                        name=row['name'],
                        slug=slugify(row['name'])
                    )
                )
            Tag.objects.bulk_create(tags, ignore_conflicts=True)
        self.stdout.write(
            self.style.SUCCESS('Теги успешно импортированы')
        )
