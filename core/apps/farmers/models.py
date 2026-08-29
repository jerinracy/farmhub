from django.conf import settings
from django.db import models


class FarmerProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="farmer_profile",
        limit_choices_to={"role": "FARMER"},
    )
    farm = models.ForeignKey(
        "farms.Farm",
        on_delete=models.CASCADE,
        related_name="farmers",
    )
    national_id = models.CharField(
        max_length=50,
        blank=True,
    )
    address = models.CharField(
        max_length=255,
        blank=True,
    )
    onboarded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="onboarded_farmers",
    )
    joined_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-joined_at"]

    def __str__(self):
        return f"{self.user.username} - {self.farm.name}"
