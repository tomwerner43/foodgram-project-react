from django.conf import settings
from django.contrib import admin

from .models import Follow, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """
    Класс модели Users.
    """

    search_fields = ("email", "first_name")
    list_filter = ("email", "first_name")
    empty_value_display = "-пусто-"


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    """
    Класс модели Follow.
    """

    empty_value_display = settings.ADMIN_SITE_HEADER
