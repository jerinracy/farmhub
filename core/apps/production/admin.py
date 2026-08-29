from django.contrib import admin

from .models import MilkProduction


@admin.register(MilkProduction)
class MilkProductionAdmin(admin.ModelAdmin):
    list_display = (
        "cow",
        "farm",
        "farmer",
        "date",
        "session",
        "quantity_liters",
        "recorded_at",
    )
    list_filter = (
        "session",
        "date",
        "farm",
        "recorded_at",
    )
    search_fields = (
        "cow__tag_id",
        "farm__name",
        "farmer__username",
        "farmer__email",
    )
    readonly_fields = (
        "recorded_at",
    )
