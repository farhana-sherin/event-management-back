from django.db import models

from django.contrib.auth.models import AbstractUser
from users.manager import UserManager


class User(AbstractUser):
    
    email=models.EmailField(unique=True,max_length=255, error_messages={'unique':'email already exist'})
    username = models.CharField(max_length=150, unique=True, default='user_default')
    phone = models.CharField(max_length=15, blank=True, null=True) 

    is_customer=models.BooleanField(default=False)
    is_eventorganizer=models.BooleanField(default=False)
    is_admin=models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        db_table='user_user'
        verbose_name='user'
        verbose_name_plural='users'
        ordering =['-id']

    def __str__(self):
        return self.email
