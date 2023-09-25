from django_filters import rest_framework as filters
from rest_framework.exceptions import AuthenticationFailed

from recipes.models import Recipe, Tag


class RecipeFilter(filters.FilterSet):

    tags = filters.ModelMultipleChoiceFilter(
        field_name="tags__slug",
        to_field_name="slug",
        queryset=Tag.objects.all(),
        label="Выберите один тег или несколько тегов",
    )
    is_favorited = filters.BooleanFilter(
        method='filter_is_favorited',
        label="В Избранном",
    )
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart',
        label="В корзине",
    )

    class Meta:
        model = Recipe
        fields = ("author", "tags", 'is_favorited', 'is_in_shopping_cart')

    def filter_is_favorited(self, queryset, name, value):
        if self.request.user.is_anonymous:
            raise AuthenticationFailed({'errors': 'Вам нужно авторизоваться!'})
        if value:
            return queryset.filter(
                in_favorite__recipe_subscriber=self.request.user
            )
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if self.request.user.is_anonymous:
            raise AuthenticationFailed({'errors': 'Вам нужно авторизоваться!'})
        if value:
            return queryset.filter(shopping_cart__cart_owner=self.request.user)
        return queryset
