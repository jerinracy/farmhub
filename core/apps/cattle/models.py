from django.conf import settings
from django.db import models


class Cow(models.Model):
    GENDER_CHOICES = [
        ("M", "Male"),
        ("F", "Female"),
    ]

    tag_id = models.CharField(
        max_length=50,
        unique=True,
    )
    farm = models.ForeignKey(
        "farms.Farm",
        on_delete=models.CASCADE,
        related_name="cows",
    )
    farmer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cows",
        limit_choices_to={"role": "FARMER"},
    )
    breed = models.CharField(
        max_length=100,
    )
    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES,
    )
    date_of_birth = models.DateField(
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(
        default=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["farm", "farmer"]),
        ]

    def save(self, *args, **kwargs):
        if not self.farm_id and self.farmer_id:
            if (
                hasattr(self.farmer, "farmer_profile")
                and self.farmer.farmer_profile.farm_id
            ):
                self.farm = self.farmer.farmer_profile.farm
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.tag_id} ({self.breed})"
