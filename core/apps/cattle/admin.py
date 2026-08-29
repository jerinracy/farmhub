from django.contrib import admin

from .models import Cow


@admin.register(Cow)
class CowAdmin(admin.ModelAdmin):
    list_display = (
        "tag_id",
        "breed",
        "gender",
        "farm",
        "farmer",
        "is_active",
        "created_at",
    )
    list_filter = (
        "gender",
        "is_active",
        "farm",
        "breed",
        "created_at",
    )
    search_fields = (
        "tag_id",
        "breed",
        "farmer__username",
        "farmer__email",
        "farm__name",
    )
    readonly_fields = ("created_at",)
