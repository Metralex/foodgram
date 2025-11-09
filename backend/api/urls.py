from django.urls import include, path
from rest_framework.routers import SimpleRouter

from . import views

app_name = "api"

api_router = SimpleRouter()

VIEWSET_REGISTRATIONS = [
    ('recipes', views.RecipeViewSet),
    ('ingredients', views.IngredientViewSet),
    ('tags', views.TagViewSet),
    ('users', views.UserViewSet),
]

for endpoint_prefix, viewset_class in VIEWSET_REGISTRATIONS:
    api_router.register(endpoint_prefix, viewset_class, basename=endpoint_prefix)

urlpatterns = [
    path("", include(api_router.urls)),
    path("auth/", include("djoser.urls.authtoken")),
]
