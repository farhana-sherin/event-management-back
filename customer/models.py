from django.db import models
from users.models import User
from organizer.models import Event


class Customer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    
        

    def __str__(self):
        return self.user.email



#add to wishlist model
class Wishlist(models.Model):
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        
        db_table = 'wishlist_table'
        verbose_name = 'wishlist'
        verbose_name_plural = 'wishlists'

    def __str__(self):
        return f"{self.customer} - {self.event}"


class Notification(models.Model):
    ROLE_CHOICES = [
        ("ADMIN", "Admin"),
        ("ORGANIZER", "Organizer"),
    ]

    sender_role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    organizer = models.ForeignKey(
        "organizer.Organizer", null=True, blank=True, on_delete=models.CASCADE
    )
    customer = models.ForeignKey(
        "customer.Customer", null=True, blank=True, on_delete=models.CASCADE, related_name="notifications"
    )

    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # Safely get the recipient
        if self.customer and self.customer.user:
            recipient = self.customer.user.email
        elif self.organizer and self.organizer.user:
            recipient = self.organizer.user.email
        else:
            recipient = "Unknown"
        return f"{self.sender_role} → {recipient} : {self.title}"




class SupportTicket(models.Model):
    STATUS_CHOICES = [
        ("OPEN", "Open"),
        ("IN_PROGRESS", "In Progress"),
        ("RESOLVED", "Resolved"),
        ("CLOSED", "Closed"),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="support_tickets")
    subject = models.CharField(max_length=255)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="OPEN")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Ticket {self.id} - {self.subject}"


class FAQ(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.question



class EventRating(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="ratings")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField()  
    review = models.TextField(blank=True, null=True)

    class Meta:
        
        db_table = 'event_rating_table'
        verbose_name = 'event rating'
        verbose_name_plural = 'event ratings'

    def __str__(self):
        return f"{self.event.title} - {self.user.username}: {self.rating}"


class Banner(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(blank=True, null=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="banners")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class TicketReply(models.Model):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name="replies")
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reply by {self.sender.username} on {self.ticket.subject}"



    
    
    
