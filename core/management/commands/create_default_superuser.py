import os

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """
    Creates one default admin account if it doesn't exist yet.

    Safe to run on every deploy: if the account is already there, it does
    nothing (it never resets an existing password). Username and password
    come from ADMIN_USERNAME / ADMIN_PASSWORD env vars when set, otherwise
    fall back to admin / admin123 so it works locally with zero setup.
    """

    help = "Creates the default admin account (admin/admin123 unless overridden by env vars) if it doesn't exist yet."

    def handle(self, *args, **options):
        username = os.environ.get("ADMIN_USERNAME", "admin")
        password = os.environ.get("ADMIN_PASSWORD", "admin123")
        email = os.environ.get("ADMIN_EMAIL", "")

        if User.objects.filter(username=username).exists():
            self.stdout.write(f"Admin '{username}' already exists — skipping.")
            return

        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(self.style.SUCCESS(f"Created default admin account: {username}"))
