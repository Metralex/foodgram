from django.db import migrations, models
import random
import string

# Генерация случайного кода для short_url_code
def generate_short():
    # Просто пример кода генерации случайной строки
    length = 6
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def set_short_url_code(apps, schema_editor):
    Recipe = apps.get_model('recipes', 'Recipe')  # Получаем модель через ORM миграции
    for recipe in Recipe.objects.all():
        recipe.short_url_code = generate_short()  # Генерация и присваивание кода
        recipe.save()

class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0002_alter_recipeingredient_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipe',
            name='short_url_code',
            field=models.SlugField(
                max_length=6,
                unique=True,
                verbose_name='Код рецепта',
                null=True,  # Временно разрешаем NULL, чтобы добавить поле
            ),
        ),
        migrations.RunPython(set_short_url_code),  # Заполняем значениями
        migrations.AlterField(
            model_name='recipe',
            name='short_url_code',
            field=models.SlugField(
                max_length=6,
                unique=True,
                verbose_name='Код рецепта',
            ),
        ),
    ]