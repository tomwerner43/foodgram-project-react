from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import F
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from recipes.models import (
    Favorite,
    Cart,
    Ingredient,
    IngredientForRecipe,
    Recipe,
    Tag)
from rest_framework import serializers

import webcolors
from users.models import Follow

User = get_user_model()


class CustomUserSerializer(UserSerializer):
    """
    Сериализатор пользователей для операции [GET].
    """

    is_subscribed = serializers.SerializerMethodField(
        method_name="get_is_subscribed")

    class Meta:
        model = User
        fields = ("email", "id", "username", "first_name",
                  "last_name", "is_subscribed")

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        if request is None or request.user.is_anonymous:
            return False
        return Follow.objects.filter(user=request.user, author=obj).exists()


class CustomUserPostSerializer(UserCreateSerializer):
    """
    Сериализатор пользователей для операции [POST].
    """

    class Meta:
        model = User
        fields = ("email", "id", "username",
                  "first_name", "last_name", "password")


class PasswordSerializer(serializers.Serializer):
    """
    Сериализатор смены пароля пользователя.
    """

    new_password = serializers.CharField(required=True)
    current_password = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ("email", "id", "username", "first_name",
                  "last_name", "is_subscribed")


class RecipePartSerializer(serializers.ModelSerializer):
    """
    Сериализатор рецепта для списка подписок.
    """

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class FollowSerializer(serializers.ModelSerializer):
    """
    Сериализатор подписок пользователя.
    """

    email = serializers.ReadOnlyField(source="author.email")
    id = serializers.ReadOnlyField(source="author.id")
    username = serializers.ReadOnlyField(source="author.username")
    first_name = serializers.ReadOnlyField(source="author.first_name")
    last_name = serializers.ReadOnlyField(source="author.last_name")
    is_subscribed = serializers.SerializerMethodField(
        method_name="get_is_subscribed")
    recipes = serializers.SerializerMethodField(method_name="get_recipes")
    recipes_count = serializers.SerializerMethodField(
        method_name="get_recipes_count")

    class Meta:
        model = Follow
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
        )

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        return Follow.objects.filter(
            author=obj.author, user=request.user).exists()

    def get_recipes(self, obj):
        request = self.context.get("request")
        if request.GET.get("recipe_limit"):
            recipe_limit = int(request.GET.get("recipe_limit"))
            queryset = Recipe.objects.filter(author=obj.author)[:recipe_limit]
        else:
            queryset = Recipe.objects.filter(author=obj.author)
        serializer = RecipePartSerializer(queryset, read_only=True, many=True)
        return serializer.data

    def get_recipes_count(self, obj):
        return obj.author.recipes.count()


class FollowToSerializer(serializers.ModelSerializer):
    """
    Сериализатор подписки/отписки от пользователя.
    """

    class Meta:
        model = Follow
        fields = ("user", "author")

    def validate(self, data):
        user = data.get("user")
        author = data.get("author")
        if user == author:
            raise serializers.ValidationError("Unable to follow yourself.")
        if Follow.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError("Already followed.")
        return data

    def to_representation(self, instance):
        request = self.context.get("request")
        context = {"request": request}
        serializer = FollowSerializer(instance, context=context)
        return serializer.data


class HexColorField(serializers.CharField):
    """
    Поле для сериализации и десериализации hex-кода цвета.
    """

    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        try:
            data = webcolors.hex_to_name(data)
        except ValueError:
            raise serializers.ValidationError("Для этого цвета нет имени")
        return data


class TagSerializer(serializers.ModelSerializer):
    """
    Сериализатор тегов.
    """

    color = HexColorField()

    class Meta:
        model = Tag
        fields = ("id", "name", "color", "slug")
        read_only_fields = ("id", "name", "slug")


class IngredientSerializer(serializers.ModelSerializer):
    """
    Сериализатор ингредиентов.
    """

    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")
        read_only_fields = ("id", "name", "measurement_unit")


class AddIngredientSerializer(serializers.ModelSerializer):
    """
    Сериализатор добавления ингредиентов в рецепт.
    """

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source="ingredient"
    )
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientForRecipe
        fields = ("id", "amount")


class IngredientAmountSerializer(serializers.ModelSerializer):
    """
    Сериализатор ингредиентов с указанием количества.
    """

    id = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(
        source="ingredient.measurement_unit")

    class Meta:
        model = IngredientForRecipe
        fields = ("id", "name", "measurement_unit", "amount")


class RecipeGetSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)


class RecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор рецептов.
    """

    author = CustomUserSerializer()
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True)
    ingredients = IngredientAmountSerializer(
        source="ingredient_in_recipe", read_only=True, many=True
    )
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField(
        method_name="get_is_favorited")
    is_in_shopping_cart = serializers.SerializerMethodField(
        method_name="get_is_in_shopping_cart"
    )

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "name",
            "author",
            "ingredients",
            "image",
            "text",
            "cooking_time",
            "is_favorited",
            "is_in_shopping_cart",
        )

    def is_exists_in(self, obj, model):
        request = self.context.get("request")
        if request is None or request.user.is_anonymous:
            return False
        return model.objects.filter(user=request.user, recipe=obj).exists()

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        return user.is_authenticated and Favorite.objects.filter(
            user=user,
            recipe=obj
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        return user.is_authenticated and Cart.objects.filter(
            user=user,
            recipe=obj
        ).exists()

    def to_representation(self, instance):
        serializer = RecipeGetSerializer(instance)
        return serializer.data


class RecipeAddSerializer(serializers.ModelSerializer):
    """
    Сериализатор добавления рецепта.
    """

    image = Base64ImageField(max_length=None, use_url=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = AddIngredientSerializer(
        many=True, source="ingredient_in_recipe")
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True)

    class Meta:
        model = Recipe
        fields = [
            "id",
            "tags",
            "author",
            "ingredients",
            "name",
            "image",
            "text",
            "cooking_time",
        ]

    def bulk_create_ingredients(self, ingredients, recipe):
        bulk_list = list()
        double_ing_check = set()
        for ingredient in ingredients:
            amount1 = ingredient["amount"]
            ingredient1 = ingredient["ingredient"]
            if ingredient1 in double_ing_check:
                raise serializers.ValidationError(
                    {
                        "error": "You can not add the same"
                        " ingredient twice."
                        "Change amount."
                    }
                )
            else:
                double_ing_check.add(ingredient1)
            bulk_list.append(
                IngredientForRecipe(
                    recipe=recipe, ingredient=ingredient1, amount=amount1
                )
            )
        IngredientForRecipe.objects.bulk_create(bulk_list)

    @transaction.atomic
    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')

        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)

        for ingredient_data in ingredients:
            ingredient = Ingredient.objects.get(id=ingredient_data['id'])
            amount = ingredient_data['amount']
            existing_recipe_ingredient = IngredientForRecipe.objects.filter(
                recipe=recipe, ingredient=ingredient).first()
            if existing_recipe_ingredient:
                existing_recipe_ingredient.amount += amount
                existing_recipe_ingredient.save()
            else:
                IngredientForRecipe.objects.create(
                    recipe=recipe, ingredient=ingredient, amount=amount)

        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance = super().update(instance, validated_data)
        instance.tags.clear()
        instance.tags.set(tags)

        IngredientForRecipe.objects.filter(recipe=instance).delete()
        for ingredient_data in ingredients:
            ingredient = Ingredient.objects.get(id=ingredient_data['id'])
            amount = ingredient_data['amount']

            recipe_ingredient, created = IngredientForRecipe.objects.get_or_create(
                recipe=instance,
                ingredient=ingredient,
                defaults={'amount': amount}
            )

            if not created:
                recipe_ingredient.amount = F('amount') + amount
                recipe_ingredient.save()

        return instance

    def to_representation(self, instance):
        serializer = RecipeGetSerializer(
            instance, context={"request": self.context.get("request")}
        )
        return serializer.data
