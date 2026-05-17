import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Ensure exactly one superuser exists for deployment."

    def handle(self, *args, **options):
        username = os.getenv("DJANGO_SUPERUSER_USERNAME", "CONIE")
        email = os.getenv("DJANGO_SUPERUSER_EMAIL", "rconieclaire@gmail.com")
        password = os.getenv("DJANGO_SUPERUSER_PASSWORD", "Conie@12345")

        User = get_user_model()
        admin, _ = User.objects.get_or_create(username=username, defaults={"email": email})
        admin.email = email
        admin.is_staff = True
        admin.is_superuser = True
        admin.is_active = True
        admin.set_password(password)
        admin.save()

        User.objects.filter(is_superuser=True).exclude(pk=admin.pk).delete()
        User.objects.filter(is_staff=True).exclude(pk=admin.pk).update(is_staff=False)

        self.stdout.write(self.style.SUCCESS(f"Only admin account is {username}."))
