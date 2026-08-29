from django.contrib import admin

from .models import FarmerProfile


@admin.register(FarmerProfile)
class FarmerProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "farm",
        "national_id",
        "onboarded_by",
        "joined_at",
    )
    list_filter = (
        "farm",
        "joined_at",
    )
    search_fields = (
        "user__username",
        "user__email",
        "user__phone_number",
        "national_id",
        "farm__name",
    )
    readonly_fields = ("joined_at",)
