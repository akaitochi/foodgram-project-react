from django.contrib import admin
from django.contrib.admin import display

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'measurement_unit',
    )
    search_fields = ('name', )
    list_filter = ('name', )


class RecipeIngredientInline(admin.TabularInline):

    model = RecipeIngredient
    extra = 2


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Класс админ-панели, отвечающий за теги."""

    list_display = (
        'name',
        'color',
        'slug'
    )
    list_filter = ('name', 'color',)
    search_fields = ('name', 'color',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Класс админ-панели, отвечающий за рецепты."""

    list_display = ('name', 'author', 'added_in_favorites',)
    search_fields = ('author', 'name', 'pub_date')
    list_filter = ('author', 'name', 'tags',)
    inlines = [
        RecipeIngredientInline,
    ]

    @display(description='Добавили в избранное')
    def added_in_favorites(self, obj):
        return obj.favorites.count()


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'recipe',
    )
    list_filter = ('user', 'recipe',)
    search_fields = ('user', 'recipe',)


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'recipe',
    )
    list_filter = ('user', 'recipe',)
    search_fields = ('user', 'recipe',)
