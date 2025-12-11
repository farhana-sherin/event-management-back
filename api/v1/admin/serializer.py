from rest_framework import serializers
from django.conf import settings
from users.models import User
from customer.models import *
from organizer.models import *
from payments.models import *

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone', 'is_customer', 'is_eventorganizer', 'is_admin']





class NotificationSerializer(serializers.ModelSerializer):
    recipient_email = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ['id', 'sender_role', 'title', 'message', 'is_read', 'created_at', 'recipient_email']

    def get_recipient_email(self, obj):
        if obj.customer and obj.customer.user:
            return obj.customer.user.email
        elif obj.organizer and obj.organizer.user:
            return obj.organizer.user.email
        return "Unknown"


class SupportTicketSerializer(serializers.ModelSerializer):
    customer_email = serializers.SerializerMethodField()

    class Meta:
        model = SupportTicket
        fields = ['id', 'subject', 'customer_email', 'status', 'created_at', 'updated_at']

    def get_customer_email(self, obj):
        return obj.customer.user.email if obj.customer and obj.customer.user else "Unknown"


class TicketReplySerializer(serializers.ModelSerializer):
    sender_email = serializers.SerializerMethodField()

    class Meta:
        model = TicketReply
        fields = ['id', 'ticket', 'sender_email', 'message', 'created_at']

    def get_sender_email(self, obj):
        return obj.sender.email if obj.sender else "Unknown"


class SendNotificationSerializer(serializers.Serializer):
    sender_role = serializers.ChoiceField(choices=[("ADMIN", "Admin")])
    title = serializers.CharField(max_length=255)
    message = serializers.CharField()
    target_group = serializers.ChoiceField(choices=[("CUSTOMERS", "Customers"), ("ORGANIZERS", "Organizers"),("ALL","all")])


class BannerSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    start_date = serializers.DateField(source='event.start_date', read_only=True)
    end_date = serializers.DateField(source='event.end_date', read_only=True)

    class Meta:
        model = Banner
        fields = ['id', 'title', 'description', 'image', 'event', 'start_date', 'end_date']
    
    def get_image(self, obj):
        if obj.image:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.image.url)
            # Fallback: construct URL manually if request is not available
            base_url = getattr(settings, 'BASE_URL', 'https://event-management-back-1jat.onrender.com')
            return f"{base_url}{obj.image.url}"
        return None 

