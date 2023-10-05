from django.contrib import admin

from .models import (
    Cart,
    Favorite,
    Ingredient,
    IngredientForRecipe,
    Recipe,
    Tag)


class IngredientsInLine(admin.TabularInline):
    """
    Встраиваемая панель администратора для модели Ingredients.
    """

    model = Recipe.ingredients.through


class TagsInLine(admin.TabularInline):
    """
    Встраиваемая панель администратора для модели Tags.
    """

    model = Recipe.tags.through


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """
    Административный класс для модели Tag.
    """

    fields = ("name", "color", "slug")


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """
    Административный класс для модели Ingredient.
    """

    list_filter = ("name",)
    list_display = ("name", "measurement_unit")


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """
    Административный класс для модели Recipe.
    """

    list_display = ("name", "author", "count_favorite")
    list_filter = ("name", "author", "tags")
    inlines = (IngredientsInLine, TagsInLine)

    def count_favorite(self, instance):
        return instance.favorites.count()


@admin.register(IngredientForRecipe)
class IngredientForRecipe(admin.ModelAdmin):
    """
    Административный класс для модели IngredientForRecipe.
    """

    list_display = ("ingredient", "recipe", "amount")


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """
    Административный класс для модели Favorite.
    """

    list_display = ("recipe", "user")


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    """
    Административный класс для модели Cart.
    """

    list_display = ("recipe", "user")
