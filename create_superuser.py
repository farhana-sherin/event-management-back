# -----------------------------
# AUTO CREATE SUPERUSER ON RENDER
# -----------------------------
import os
from django.contrib.auth import get_user_model

if os.environ.get("CREATE_SUPERUSER") == "1":
    User = get_user_model()

    email = "admin123@gmail.com"
    username = "admin"   # required for your model
    password = "1234"

    if not User.objects.filter(email=email).exists():
        User.objects.create_superuser(
            email=email,
            username=username,
            password=password
        )
        print("Superuser created with email login!")
    else:
        print("Superuser already exists!")
