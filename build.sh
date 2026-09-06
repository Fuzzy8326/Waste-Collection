#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

# Creates/updates an admin user from DJANGO_SUPERUSER_* env vars.
# Safe to leave in permanently - does nothing if those vars aren't set.
python manage.py create_admin