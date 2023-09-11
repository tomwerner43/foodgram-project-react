from django.contrib import admin

from .models import Subscribe, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """
    Класс модели Users
    """

    list_display = (
        'id',
        'username',
        'email',
        'first_name',
        'last_name',
    )
    list_filter = ('username', 'email', 'is_superuser',)
    list_display_links = ('email',)
    search_fields = ('username', 'email',)
    empty_value_display = 'пусто'


@admin.register(Subscribe)
class SubscribeAdmin(admin.ModelAdmin):
    """
    Класс модели SubscrideAdmin
    """

    list_display = (
        'id',
        'user',
        'author',
    )
    list_filter = ('user', 'author',)
    search_fields = ('user__username', 'author__username',)
    empty_value_display = 'пусто'
