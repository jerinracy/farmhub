from django.contrib import admin

from .models import CowActivity


@admin.register(CowActivity)
class CowActivityAdmin(admin.ModelAdmin):
    list_display = (
        "cow",
        "activity_type",
        "date",
        "recorded_by",
        "created_at",
    )
    list_filter = (
        "activity_type",
        "date",
        "created_at",
    )
    search_fields = (
        "cow__tag_id",
        "notes",
        "recorded_by__username",
        "recorded_by__email",
    )
    readonly_fields = ("created_at",)
