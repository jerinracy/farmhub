from django.conf import settings
from django.db import models


class ActivityType(models.TextChoices):
    VACCINATION = "VACCINATION", "Vaccination"
    BIRTH = "BIRTH", "Birth"
    HEALTH_CHECK = "HEALTH_CHECK", "Health Check"
    OTHER = "OTHER", "Other"


class CowActivity(models.Model):
    ActivityType = ActivityType

    cow = models.ForeignKey(
        "cattle.Cow",
        on_delete=models.CASCADE,
        related_name="activities",
    )
    activity_type = models.CharField(
        max_length=30,
        choices=ActivityType.choices,
    )
    date = models.DateField()
    notes = models.TextField(
        blank=True,
    )
    details = models.JSONField(
        default=dict,
        blank=True,
    )
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recorded_activities",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-date", "-created_at"]
        indexes = [
            models.Index(fields=["cow", "activity_type", "date"]),
        ]

    def __str__(self):
        return f"{self.cow.tag_id} - {self.activity_type} on {self.date}"
