"""URL configuration for gateway API endpoints."""
from django.urls import include, path
from rest_framework.routers import SimpleRouter

from . import views

app_name = 'gateway'

router = SimpleRouter()

router.register(
    prefix='accounts',
    viewset=views.AccountEndpoint,
    basename='accounts'
)

router.register(
    prefix='categories',
    viewset=views.CategoryEndpoint,
    basename='categories'
)

router.register(
    prefix='components',
    viewset=views.ComponentEndpoint,
    basename='components'
)

router.register(
    prefix='items',
    viewset=views.CulinaryItemEndpoint,
    basename='items'
)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
