import os
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """
    Create (or update) a superuser from environment variables.

    Reads DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL, and
    DJANGO_SUPERUSER_PASSWORD from the environment. Safe to run on
    every deploy - if the user already exists, it just makes sure
    they're still a superuser/staff and updates the password.

    Does nothing (and does not error) if the env vars aren't set,
    so it's safe to leave in build.sh permanently.
    """

    help = "Create a superuser from DJANGO_SUPERUSER_* environment variables."

    def handle(self, *args, **options):
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '')

        if not username or not password:
            self.stdout.write(
                'DJANGO_SUPERUSER_USERNAME / DJANGO_SUPERUSER_PASSWORD not set - skipping.'
            )
            return

        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': email},
        )
        user.email = email or user.email
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

        if created:
            self.stdout.write(self.style.SUCCESS(f"Created superuser '{username}'."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Updated existing user '{username}' to superuser."))
