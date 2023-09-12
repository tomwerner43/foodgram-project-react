from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

from users.models import User


class Tag(models.Model):
    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name='Тег',
    )

    color = models.CharField(
        max_length=7,
        default='#00FFFF',
        unique=True,
        verbose_name='Цвет (HEX-код)',
        validators=[
            RegexValidator(
                regex="^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$",
                message='Недопустимый формат цвета!',
            )
        ],
    )
    slug = models.SlugField(
        max_length=255,
        unique=True,
        verbose_name='Слаг',
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        verbose_name='Название',
        max_length=200,
    )
    measurement_unit = models.CharField(
        verbose_name='Ед. измерения',
        max_length=255,
    )

    class Meta:
        ordering = ('name',)
        constraints = [
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_ingredient_measurement_unit'
            )
        ]
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class Recipe(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='recipe',
        verbose_name='Автор',
    )
    name = models.CharField(
        max_length=200,
        verbose_name='Название',
    )
    image = models.ImageField(
        upload_to='recipes/',
        null=True,
        default=None,
        verbose_name='Изображение',
    )
    text = models.TextField(
        verbose_name='Описание',
    )
    tags = models.ManyToManyField(
        Tag,
        related_name="recipes",
        verbose_name='Тег',
    )
    cooking_time = models.PositiveSmallIntegerField(
        default=1,
        blank=False,
        verbose_name='Время приготовления (в мин.)',
        validators=[
            MinValueValidator(1, 'Время не может быть меньше или равна 0!'),
        ],
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации',
    )

    class Meta:
        ordering = ['-pub_date', ]
        constraints = [
            models.UniqueConstraint(fields=['author', 'name'],
                                    name='unique_author_recipe_name'),
        ]
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class IngredientForRecipe(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )
    amount = models.PositiveIntegerField(
        verbose_name='Количество в рецепте',
        validators=[
            MinValueValidator(1, 'Должно быть больше 0'),
        ]
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['recipe', 'ingredient'],
                                    name='unique_ingredient_recipe'),
        ]
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'

    def __str__(self):
        return f'Входит в состав {self.recipe.name}'


class Favorite(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        related_name='in_favorite',
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )
    recipe_subscriber = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite',
        verbose_name='Добавили в избранное',
    )

    class Meta:
        ordering = ("-id",)
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'recipe_subscriber'],
                name='unique_recipe_subscriber_and_recipe'
            ),
        ]
        verbose_name = 'Рецепт в списке избранного'
        verbose_name_plural = 'Рецепты в списке избранного'

    def __str__(self):
        return f"{self.recipe_subscriber} полюбил {self.recipe}"


class Cart(models.Model):
    cart_owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь корзины',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Рецепт',
    )

    class Meta:
        ordering = ("-id",)
        verbose_name = 'Рецепт в списке покупок'
        verbose_name_plural = 'Рецепты в списке покупок'

    def __str__(self):
        return self.recipe.name
