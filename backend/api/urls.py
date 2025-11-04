from django.urls import include, path
from rest_framework.routers import SimpleRouter

from . import views


# Пространство имён для API маршрутов
app_name = 'api'

# Маршрутизатор для автоматического создания URL-ов
router_v1 = SimpleRouter()

router_v1.register(
    prefix='users',
    viewset=views.UserHandler,
    basename='users'
)

router_v1.register(
    prefix='tags',
    viewset=views.ClassificationHandler,
    basename='tags'
)

router_v1.register(
    prefix='ingredients',
    viewset=views.ElementHandler,
    basename='ingredients'
)

router_v1.register(
    prefix='recipes',
    viewset=views.DishHandler,
    basename='recipes'
)


urlpatterns = [
    path('', include(router_v1.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
