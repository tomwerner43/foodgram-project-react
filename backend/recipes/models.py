from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

User = get_user_model()


class Tag(models.Model):
    """
    Класс представляет теги, которые могут быть привязаны к рецептам.
    """

    name = models.CharField(verbose_name="Тег", max_length=16, unique=True)
    color = models.CharField(
        verbose_name="Цвет (HEX-код)",
        max_length=16,
        unique=True,
        validators=[
            RegexValidator(
                regex="^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$",
                message="Недопустимый формат цвета!",
            )
        ],
    )
    slug = models.SlugField(verbose_name="Слаг", unique=True)

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"
        ordering = ("name",)

    def __str__(self):
        return f"{self.name} (цвет: {self.color})"


class Ingredient(models.Model):
    """
    Класс представляет ингредиенты, используемые в рецептах.
    """

    name = models.CharField(
        verbose_name="Название", max_length=150, db_index=True)
    measurement_unit = models.CharField(
        verbose_name="Единица измерения", max_length=10)

    class Meta:
        verbose_name = "Ингридиент"
        verbose_name_plural = "Ингридиенты"
        ordering = ("name",)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """
    Класс представляет рецепты блюд.
    """

    name = models.CharField(verbose_name="Название", max_length=400)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Автор",
        related_name="recipes",
    )
    image = models.ImageField(
        verbose_name="Изображение",
        upload_to="food/images/",
    )
    text = models.TextField(verbose_name="Описание", max_length=15000)
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name="Ингредиенты",
        through="IngredientForRecipe",
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name="Тег",
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name="Время приготовления (в мин.)",
        validators=[
            MinValueValidator(1, "Время не может быть меньше или равна 0!"),
        ],
    )
    pub_date = models.DateTimeField(
        verbose_name="Дата публикации", auto_now_add=True)

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        ordering = ("-pub_date",)
        constraints = (
            models.UniqueConstraint(
                fields=("name", "author"),
                name="unique_for_author",
            ),
        )

    def __str__(self):
        return f"{self.name}. Автор: {self.author.username}"


class IngredientForRecipe(models.Model):
    """
    Класс представляет отношение между ингредиентами
    и рецептами, указывая количество ингредиентов в каждом рецепте.
    """

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="ingredient_in_recipe",
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name="recipes_with_ingredient",
    )
    amount = models.PositiveSmallIntegerField(
        "Количество в рецепте",
        default=1,
        validators=(
            MinValueValidator(
                1,
                message="Должно быть больше 0"),))

    class Meta:
        verbose_name = "Ингредиент в рецепте"
        verbose_name_plural = "Ингредиенты в рецепте"

    def __str__(self):
        return f"{self.amount} {self.ingredient.name}"


class Favorite(models.Model):
    """
    Класс представляет отношение между пользователями
    и рецептами, которые они добавили в избранное.
    """

    recipe = models.ForeignKey(
        Recipe,
        verbose_name="Рецепт",
        on_delete=models.CASCADE,
        related_name="favorites",
    )
    user = models.ForeignKey(
        User,
        verbose_name="Пользователь",
        on_delete=models.CASCADE,
        related_name="favorites",
    )

    class Meta:
        verbose_name = "Рецепт в списке избранного"
        verbose_name_plural = "Рецепты в списке избранного"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="already in favorite"
            )
        ]

    def __str__(self) -> str:
        return f"{self.user} -> {self.recipe}"


class Cart(models.Model):
    """
    Класс представляет отношение между пользователями
    и рецептами, которые они добавили в список покупок.
    """

    recipe = models.ForeignKey(
        Recipe,
        verbose_name="Рецепт",
        on_delete=models.CASCADE,
        related_name="shopping_cart",
    )
    user = models.ForeignKey(
        User,
        verbose_name="Пользователь",
        on_delete=models.CASCADE,
        related_name="shopping_cart",
    )

    class Meta:
        verbose_name = "Рецепт в списке покупок"
        verbose_name_plural = "Рецепты в списке покупок"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="already in cart")
        ]

    def __str__(self) -> str:
        return (f'{self.user.username} добавил рецепт'
                f'"{self.recipe.name}" в избранное')
