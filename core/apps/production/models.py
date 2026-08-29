from django.conf import settings
from django.db import models


class MilkProduction(models.Model):
    SESSION_CHOICES = [
        ("MORNING", "Morning"),
        ("EVENING", "Evening"),
    ]

    cow = models.ForeignKey(
        "cattle.Cow",
        on_delete=models.CASCADE,
        related_name="milk_records",
    )
    farm = models.ForeignKey(
        "farms.Farm",
        on_delete=models.CASCADE,
        related_name="milk_records",
    )
    farmer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="milk_records",
    )
    date = models.DateField()
    quantity_liters = models.DecimalField(
        max_digits=6,
        decimal_places=2,
    )
    session = models.CharField(
        max_length=10,
        choices=SESSION_CHOICES,
        default="MORNING",
    )
    recorded_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-date", "-recorded_at"]
        unique_together = ("cow", "date", "session")
        indexes = [
            models.Index(fields=["farm", "date"]),
            models.Index(fields=["farmer", "date"]),
        ]

    def save(self, *args, **kwargs):
        if self.cow_id:
            if not self.farm_id and hasattr(self.cow, "farm_id"):
                self.farm_id = self.cow.farm_id
            if not self.farmer_id and hasattr(self.cow, "farmer_id"):
                self.farmer_id = self.cow.farmer_id
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.cow.tag_id} - {self.date} {self.session}: {self.quantity_liters}L"
