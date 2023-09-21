from datetime import datetime

from django.db.models import Sum
from django.shortcuts import HttpResponse, get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.fields import Field
from rest_framework.response import Response
from book.models import (
    Favorite,
    Ingredient,
    IngredientForRecipe,
    Recipe,
    Cart,
    Tag
)

from .filters import RecipeFilter
from .pagination import CustomPagination
from .permissions import IsAuthorOrAdminOrReadOnly
from .serializers import (
    FavoriteRecipeSerializer,
    IngredientSerializer,
    RecipeCRUDSerializer,
    CartSerializer,
    TagSerializer
)


class ReadOnlyMixin(Field):
    """
    Mixin, который делает все поля модели только для чтения.
    """

    def __new__(cls, *args, **kwargs):
        setattr(
            cls.Meta,
            'read_only_fields',
            [f.name for f in cls.Meta.model._meta.get_fields()],
        )
        return super(ReadOnlyMixin, cls).__new__(cls, *args, **kwargs)


class CustomListRecipeDeleteMixin(mixins.DestroyModelMixin):
    """
    Mixin, который добавляет функциональность удаления элементов из списка.
    """

    def destroy(self, request, *args, **kwargs):
        model = kwargs.get('model')
        args = {
            'recipe': self.kwargs.get('recipe_id'),
            kwargs.get('fkey'): self.request.user
        }

        if not model.objects.filter(**args):
            return Response(
                {'errors': 'Данный рецепт не добавлен в список!'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        instance = get_object_or_404(model, **args)
        instance_name = instance.recipe.name
        self.perform_destroy(instance)
        return Response(
            {'success': f'Данный рецепт {instance_name} '
             'удален из вашего списка!'},
            status=status.HTTP_204_NO_CONTENT,
        )

    def perform_destroy(self, instance):
        instance.delete()


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для модели Tag,
    который предоставляет только операции чтения данных.
    """

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny, )
    pagination_class = None
    filter_backends = (DjangoFilterBackend, filters.SearchFilter,
                       filters.OrderingFilter)
    search_fields = ('^name',)
    ordering_fields = ('name', 'slug', )
    http_method_names = ('get', )


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для модели Ingredient,
    который предоставляет только операции чтения данных.
    """

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    permission_classes = (AllowAny, )
    filter_backends = (DjangoFilterBackend, filters.SearchFilter,
                       filters.OrderingFilter)
    search_fields = ('^name', )
    ordering_fields = ('name', 'measurement_unit', )
    http_method_names = ('get', )


class RecipeViewSet(viewsets.ModelViewSet):
    """
    ViewSet для модели Recipe, которое поддерживает операции CRUD.
    """

    queryset = Recipe.objects.all()
    serializer_class = RecipeCRUDSerializer
    pagination_class = CustomPagination
    permission_classes = (IsAuthorOrAdminOrReadOnly, )
    filter_backends = (DjangoFilterBackend, )
    filterset_class = RecipeFilter
    http_method_names = ('get', 'post', 'patch', 'delete', )


class FavoriteViewSet(mixins.CreateModelMixin,
                      CustomListRecipeDeleteMixin,
                      viewsets.GenericViewSet):
    """
    ViewSet для модели Favorite, позволяющее
    пользователям добавлять рецепты в избранное и удалять их оттуда.
    """

    queryset = Favorite.objects.all()
    serializer_class = FavoriteRecipeSerializer
    permission_classes = (IsAuthenticated, )
    http_method_names = ('post', 'delete', )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'recipe_id': self.kwargs.get('recipe_id')})
        return context

    def perform_create(self, serializer):
        recipe = get_object_or_404(
            Recipe,
            pk=self.kwargs.get('recipe_id'),
        )
        serializer.save(
            recipe_subscriber=self.request.user,
            recipe=recipe,
        )

    def delete(self, request, recipe_id):
        return super().destroy(
            self,
            request,
            model=Favorite,
            fkey='recipe_subscriber'
        )


class CartViewSet(mixins.CreateModelMixin,
                  CustomListRecipeDeleteMixin,
                  viewsets.GenericViewSet):
    """
    ViewSet для модели Cart,
    где пользователи могут добавлять рецепты в свою корзину покупок
    и удалять их оттуда. Также есть функциональность для скачивания
    списка покупок в виде текстового файла.
    """

    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = (IsAuthenticated, )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        recipe = get_object_or_404(
            Recipe,
            pk=self.kwargs.get('recipe_id')
        )
        context.update({'recipe': recipe})
        context.update({'cart_owner': self.request.user})
        return context

    def delete(self, request, recipe_id):
        return super().destroy(
            self,
            request,
            model=Cart,
            fkey='cart_owner'
        )

    @staticmethod
    def download_shopping_cart(request):
        if not Cart.objects.filter(cart_owner=request.user):
            return Response({'errors': 'Ваша корзина пуста!'},
                            status=status.HTTP_400_BAD_REQUEST)
        shopping_cart = IngredientForRecipe.objects.filter(
            recipe__shopping_cart__cart_owner=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit',
        ).annotate(
            total=Sum('amount')
        )

        text = f'Список покупкна {datetime.now().strftime("%d.%m.%Y")}:\n\n'
        for ingredient in shopping_cart:
            text += (f'{ingredient["ingredient__name"]}: '
                     f'{ingredient["total"]}'
                     f'{ingredient["ingredient__measurement_unit"]}\n')

        response = HttpResponse(text, content_type='text/plain')
        filename = f'shopping_list_{datetime.now().strftime("%d.%m.%Y")}.txt'
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response
