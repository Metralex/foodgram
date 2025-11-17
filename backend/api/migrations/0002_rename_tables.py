"""Переименование таблиц из api в users и recipes."""

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('api', '0001_initial'),
        ('users', '0001_initial'),
        ('recipes', '0001_initial'),
    ]

    operations = [
        # Переименование таблиц users
        migrations.RunSQL(
            sql="ALTER TABLE api_user RENAME TO users_user;",
            reverse_sql="ALTER TABLE users_user RENAME TO api_user;",
        ),
        migrations.RunSQL(
            sql="ALTER TABLE api_subscription RENAME TO users_subscription;",
            reverse_sql="ALTER TABLE users_subscription RENAME TO api_subscription;",
        ),
        # Переименование таблиц recipes
        migrations.RunSQL(
            sql="ALTER TABLE api_tag RENAME TO recipes_tag;",
            reverse_sql="ALTER TABLE recipes_tag RENAME TO api_tag;",
        ),
        migrations.RunSQL(
            sql="ALTER TABLE api_ingredient RENAME TO recipes_ingredient;",
            reverse_sql="ALTER TABLE recipes_ingredient RENAME TO api_ingredient;",
        ),
        migrations.RunSQL(
            sql="ALTER TABLE api_recipe RENAME TO recipes_recipe;",
            reverse_sql="ALTER TABLE recipes_recipe RENAME TO api_recipe;",
        ),
        migrations.RunSQL(
            sql="ALTER TABLE api_recipeingredient RENAME TO recipes_recipeingredient;",
            reverse_sql="ALTER TABLE recipes_recipeingredient RENAME TO api_recipeingredient;",
        ),
        migrations.RunSQL(
            sql="ALTER TABLE api_favorite RENAME TO recipes_favorite;",
            reverse_sql="ALTER TABLE recipes_favorite RENAME TO api_favorite;",
        ),
        migrations.RunSQL(
            sql="ALTER TABLE api_shoppingcart RENAME TO recipes_shoppingcart;",
            reverse_sql="ALTER TABLE recipes_shoppingcart RENAME TO api_shoppingcart;",
        ),
        # Переименование промежуточных таблиц ManyToMany (если есть)
        migrations.RunSQL(
            sql="ALTER TABLE IF EXISTS api_recipe_tags RENAME TO recipes_recipe_tags;",
            reverse_sql="ALTER TABLE IF EXISTS recipes_recipe_tags RENAME TO api_recipe_tags;",
        ),
    ]