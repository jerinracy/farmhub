import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = "Seed default SuperAdmin user from environment variables if not already existing."

    def handle(self, *args, **options):
        username = os.environ.get("SUPERADMIN_USERNAME", "admin")
        email = os.environ.get("SUPERADMIN_EMAIL", "admin@farmhub.com")
        password = os.environ.get("SUPERADMIN_PASSWORD", "admin123")

        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f"SuperAdmin user '{username}' already exists.")
            )
            return

        if email and User.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.WARNING(f"SuperAdmin user with email '{email}' already exists.")
            )
            return

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            role=User.Role.SUPERADMIN,
            is_staff=True,
            is_superuser=True,
        )

        self.stdout.write(
            self.style.SUCCESS(f"Successfully created SuperAdmin user '{user.username}'.")
        )
