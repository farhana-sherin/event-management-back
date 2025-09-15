from django.db import models
from users.models import User




class Organizer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    phone = models.CharField(max_length=15, blank=True, null=True)




    class Meta:
        db_table = 'organizer'
        verbose_name = 'organizer'
        verbose_name_plural = 'organizers'
        ordering = ['-id']

    def __str__(self):
        return self.user.email


class Event(models.Model):
    CATEGORY_CHOICES = [
        ('MUSIC', 'music'),
        ('SPORTS', 'sports'),
        ('TECH', 'tech'),
        ('ARTS', 'arts'),
        ('OTHER', 'other'),
    ]

    organizer = models.ForeignKey(Organizer, on_delete=models.CASCADE, related_name='events')
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='OTHER')
    location = models.CharField(max_length=255)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total_seats = models.PositiveIntegerField()
    available_seats = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    images = models.FileField(upload_to="event_images/", blank=True, null=True)
    is_active = models.BooleanField(default=False) 

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return f"{self.title} ({self.organizer.user.username})"





