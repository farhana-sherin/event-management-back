from django.db import models
from users.models import User


class Organizer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

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
    short_description = models.CharField(max_length=255, blank=True)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='OTHER')
    location = models.CharField(max_length=255)
    start_date = models.DateField(blank=True, null=True)
    start_time = models.TimeField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    ticket_count = models.PositiveIntegerField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    images = models.FileField(upload_to="event_images/", blank=True, null=True)
    qr_code_text = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=False)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return f"{self.title} ({self.organizer.user.username})"
