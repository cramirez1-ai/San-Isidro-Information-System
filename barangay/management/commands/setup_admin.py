import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create the single production admin account and remove old staff/admin accounts."

    def handle(self, *args, **options):
        username = os.getenv("ADMIN_USERNAME", "admin").strip()
        email = os.getenv("ADMIN_EMAIL", "admin@sanisidro.local").strip()
        password = os.getenv("ADMIN_PASSWORD", "").strip()

        if not password:
            raise CommandError("ADMIN_PASSWORD is required to create the admin account.")

        User = get_user_model()

        User.objects.filter(is_staff=True).exclude(username=username).delete()
        User.objects.filter(is_superuser=True).exclude(username=username).delete()

        admin, created = User.objects.get_or_create(username=username)
        admin.email = email
        admin.is_active = True
        admin.is_staff = True
        admin.is_superuser = True
        admin.set_password(password)
        admin.save()

        action = "created" if created else "updated"
        self.stdout.write(self.style.SUCCESS(f"Single admin account {action}: {username}"))
