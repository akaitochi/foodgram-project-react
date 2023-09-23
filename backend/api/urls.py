from django.urls import include, path
from rest_framework import routers

from .views import FollowViewSet, IngredientViewSet, RecipeViewSet, TagViewSet

v1_router = routers.DefaultRouter()
v1_router.register('users', FollowViewSet, basename='users')
v1_router.register('ingredients', IngredientViewSet, basename='ingredients')
v1_router.register('recipes', RecipeViewSet, basename='recipes')
v1_router.register('tags', TagViewSet, basename='tags')

app_name = 'api'

urlpatterns = [
    path('', include(v1_router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
