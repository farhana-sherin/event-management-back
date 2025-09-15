from customer.models import Notification

def create_notification(customer, title, message, organizer=None, sender_role="ADMIN"):
 
    Notification.objects.create(
        customer=customer,
        title=title,
        message=message,
        organizer=organizer,
        sender_role=sender_role
    )
