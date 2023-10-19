from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import (
    FollowToView,
    FollowView,
    IngredientViewSet,
    RecipeViewSet,
    TagViewSet,
    UserViewSet,
)

app_name = "api"

router = SimpleRouter()

router.register("users", UserViewSet, basename="users")
router.register("tags", TagViewSet, basename="tags")
router.register("ingredients", IngredientViewSet, basename="ingredients")
router.register("recipes", RecipeViewSet, basename="recipes")


urlpatterns = [
    path("users/subscriptions/", FollowView.as_view()),
    path("users/<int:pk>/subscribe/", FollowToView.as_view()),
    path("", include(router.urls)),
    path("auth/", include("djoser.urls.authtoken")),
]

router.register(r"recipes/(?P<pk>\d+)/favorite",
                RecipeViewSet, basename="recipe-favorite")
router.register(r"recipes/(?P<pk>\d+)/shopping-cart",
                RecipeViewSet, basename="recipe-shopping-cart")
