from django.contrib import admin

from .models import Farm


@admin.register(Farm)
class FarmAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "location",
        "agent",
        "is_active",
        "created_at",
    )
    list_filter = (
        "is_active",
        "agent",
        "created_at",
    )
    search_fields = (
        "name",
        "location",
        "agent__username",
        "agent__email",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
    )
