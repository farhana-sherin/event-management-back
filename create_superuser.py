import os
from django.contrib.auth import get_user_model

if os.environ.get("CREATE_SUPERUSER") == "1":
    User = get_user_model()

    email = "admin123@gmail.com"
    username = "admin123"
    password = "1234"

    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        print("Superuser created!")
    else:
        print("Superuser already exists!")
