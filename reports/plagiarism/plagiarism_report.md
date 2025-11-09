# Backend/Infra Plagiarism Audit

## Summary

- Total files analysed: 52
- Matched files with similarity scores: 24
- Files only in current project: 12
- Files only in reference project: 16
- Average similarity (unweighted): 61.74%
- Average similarity weighted by file size: 88.28%

## Per-file Similarity

| Relative Path | Current | Reference | Raw % | Normalized % | Notes |
| --- | --- | --- | --- | --- | --- |
| `backend/Dockerfile` | yes | yes | 66.55% | 65.83% |  |
| `backend/api/__init__.py` | yes | yes | 0.0% | 0.0% |  |
| `backend/api/admin.py` | yes | no |  |  | Missing in reference project. |
| `backend/api/apps.py` | yes | yes | 46.85% | 48.59% |  |
| `backend/api/filters.py` | yes | yes | 55.65% | 59.07% |  |
| `backend/api/management/__init__.py` | yes | no |  |  | Missing in reference project. |
| `backend/api/management/commands/__init__.py` | yes | no |  |  | Missing in reference project. |
| `backend/api/management/commands/import_ingredients.py` | yes | no |  |  | Missing in reference project. |
| `backend/api/management/commands/import_tags.py` | yes | no |  |  | Missing in reference project. |
| `backend/api/migrations/0001_initial.py` | yes | no |  |  | Missing in reference project. |
| `backend/api/migrations/__init__.py` | yes | no |  |  | Missing in reference project. |
| `backend/api/models.py` | yes | no |  |  | Missing in reference project. |
| `backend/api/pagination.py` | yes | yes | 33.99% | 37.88% |  |
| `backend/api/permissions.py` | yes | yes | 62.0% | 61.81% |  |
| `backend/api/serializers.py` | yes | yes | 75.1% | 75.17% |  |
| `backend/api/urls.py` | yes | yes | 70.03% | 70.35% |  |
| `backend/api/utils.py` | yes | yes | 25.2% | 26.51% |  |
| `backend/api/validators.py` | yes | no |  |  | Missing in reference project. |
| `backend/api/views.py` | yes | yes | 67.55% | 67.95% |  |
| `backend/api/views_recipe.py` | yes | no |  |  | Missing in reference project. |
| `backend/backend/__init__.py` | yes | yes | 0.0% | 0.0% |  |
| `backend/backend/asgi.py` | yes | yes | 44.08% | 43.87% |  |
| `backend/backend/settings.py` | yes | yes | 60.77% | 56.86% |  |
| `backend/backend/urls.py` | yes | yes | 82.08% | 83.92% |  |
| `backend/backend/wsgi.py` | yes | yes | 43.11% | 42.84% |  |
| `backend/data/ingredients.csv` | yes | yes | 100.0% | 100.0% |  |
| `backend/data/recipes_tag.csv` | yes | yes | 100.0% | 100.0% |  |
| `backend/db/__init__.py` | yes | yes | 100.0% | 100.0% |  |
| `backend/manage.py` | yes | yes | 89.02% | 86.27% |  |
| `backend/recipes/__init__.py` | no | yes |  |  | Missing in current project. |
| `backend/recipes/admin.py` | no | yes |  |  | Missing in current project. |
| `backend/recipes/apps.py` | no | yes |  |  | Missing in current project. |
| `backend/recipes/management/__init__.py` | no | yes |  |  | Missing in current project. |
| `backend/recipes/management/commands/__init__.py` | no | yes |  |  | Missing in current project. |
| `backend/recipes/management/commands/import_ingredients.py` | no | yes |  |  | Missing in current project. |
| `backend/recipes/management/commands/import_ingredients_json.py` | no | yes |  |  | Missing in current project. |
| `backend/recipes/management/commands/import_tags.py` | no | yes |  |  | Missing in current project. |
| `backend/recipes/management/commands/import_tags_json.py` | no | yes |  |  | Missing in current project. |
| `backend/recipes/migrations/0001_initial.py` | no | yes |  |  | Missing in current project. |
| `backend/recipes/migrations/0002_alter_recipeingredient_options.py` | no | yes |  |  | Missing in current project. |
| `backend/recipes/migrations/0003_recipe_short_url_code.py` | no | yes |  |  | Missing in current project. |
| `backend/recipes/migrations/__init__.py` | no | yes |  |  | Missing in current project. |
| `backend/recipes/models.py` | no | yes |  |  | Missing in current project. |
| `backend/recipes/validators.py` | no | yes |  |  | Missing in current project. |
| `backend/recipes/views.py` | no | yes |  |  | Missing in current project. |
| `backend/requirements.txt` | yes | yes | 40.44% | 42.49% |  |
| `infra/.env` | yes | no |  |  | Missing in reference project. |
| `infra/docker-compose.production.yml` | yes | yes | 88.3% | 87.34% |  |
| `infra/docker-compose.yml` | yes | yes | 84.09% | 84.74% |  |
| `infra/nginx-dev.conf` | yes | yes | 80.16% | 78.64% |  |
| `infra/nginx.conf` | yes | yes | 66.8% | 62.95% |  |
| `infra/nginx_eda_hopto_config.txt` | yes | no |  |  | Missing in reference project. |

## High Similarity Highlights (>= 90% normalized)

- `backend/data/ingredients.csv` – 100.0% normalized similarity
- `backend/data/recipes_tag.csv` – 100.0% normalized similarity
- `backend/db/__init__.py` – 100.0% normalized similarity