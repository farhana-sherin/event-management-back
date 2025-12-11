from django.db import models
from users.models import User
from organizer.models import Event
from customer.models import Customer




from django.db import models
from users.models import User
from organizer.models import Event
from customer.models import Customer


# Booking model
class Booking(models.Model):
    STATUS_CHOICES = [
        ("CONFIRMED", "Confirmed"),
        ("CANCELLED", "Cancelled"),
    ]
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="bookings")
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="bookings")
    tickets_count = models.PositiveIntegerField(default=1)
    booking_date = models.DateTimeField(auto_now_add=True)
    qr_code_text = models.TextField(blank=True, null=True) # store QR code
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="CONFIRMED")

    class Meta:
        db_table = "booking_table"
        ordering = ["-id"]

    def __str__(self):
        return f"{self.customer.user.email} - {self.event.title}"


# Payment model
class Payment(models.Model):
    STATUS_CHOICES = [
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
        ("PENDING", "Pending"),
        ("REFUNDED", "Refunded"),
    ]

    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name="payment")
    provider = models.CharField(max_length=50)  
    payment_id = models.CharField(max_length=100)
    payment_intent_id = models.CharField(max_length=100, blank=True, null=True) 
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    receipt_url = models.URLField(blank=True)

    class Meta:
        db_table = "payment_table"
        ordering = ["-id"]

    def __str__(self):  
        return f"{self.booking.customer.user.email} - {self.status}"
