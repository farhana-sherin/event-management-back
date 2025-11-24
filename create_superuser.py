# AUTO CREATE SUPERUSER ON RENDER
import os
from django.apps import apps
from django.contrib.auth import get_user_model

def create_superuser():
    User = get_user_model()

    email = "admin123@gmail.com"
    username = "admin123"
    password = "1234"

    if not User.objects.filter(email=email).exists():
        User.objects.create_superuser(
            email=email,
            username=username,
            password=password
        )
        print("Superuser created!")
    else:
        print("Superuser already exists!")

# Only run when apps are fully loaded
if os.environ.get("CREATE_SUPERUSER") == "1":
    def _run_create_superuser(sender, **kwargs):
        create_superuser()

    from django.apps import AppConfig, apps
    from django.core.signals import request_finished
    from django.db.models.signals import post_migrate

    post_migrate.connect(_run_create_superuser)
