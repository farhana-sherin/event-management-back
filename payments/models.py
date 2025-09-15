from django.db import models
from users.models import User
from organizer.models import Event
from customer.models import Customer
import uuid


class Booking(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('CANCELLED', 'Cancelled'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='bookings',null=True,blank=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='bookings')
    tickets_count = models.PositiveIntegerField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    qr_code = models.CharField(max_length=100, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'booking_table'
        verbose_name = 'booking'
        verbose_name_plural = 'bookings'
        ordering = ['-id']

    def __str__(self):

        return self.event.title


class Payment(models.Model):
    STATUS_CHOICES = [
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('PENDING', 'Pending'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="payments",null=True,blank=True)
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name="payment")
    provider = models.CharField(max_length=50)  
    payment_id = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    receipt_url = models.URLField(blank=True)

    class Meta:
        db_table = 'payment_table'
        verbose_name = 'payment'
        verbose_name_plural = 'payments'
        ordering = ['-id']

    def __str__(self):  
        return f"{self.booking.customer.user.email} - {self.status}"
        

