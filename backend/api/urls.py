from django.urls import include, path
from rest_framework.routers import SimpleRouter

from . import views as api_views

app_name = "api"

router = SimpleRouter()

for prefix, viewset in (
    ("users", api_views.UserViewSet),
    ("tags", api_views.TagViewSet),
    ("ingredients", api_views.IngredientViewSet),
    ("recipes", api_views.RecipeViewSet),
):
    router.register(prefix, viewset, basename=prefix)

urlpatterns = [
    path("", include(router.urls)),
    path("auth/", include("djoser.urls.authtoken")),
]
