from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        SUPERADMIN = "SUPERADMIN", "Super Admin"
        AGENT = "AGENT", "Agent"
        FARMER = "FARMER", "Farmer"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.FARMER,
    )

    phone_number = models.CharField(
        max_length=20,
        blank=True,
    )

    created_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_users",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.username or self.email
