from rest_framework import serializers
from customer.models import Customer
from users.models import User
from payments.models import *
from api.v1.organizer.serializer import *



class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'user']

class BookingSerializer(serializers.ModelSerializer):
    event = EventSerializer()
    class Meta:
        model = Booking
        
        fields = [
            "id","customer","event","tickets_count","total_amount","status","qr_code","created_at"]


class WishlistSerializer(serializers.ModelSerializer):
    event = EventSerializer(read_only=True)

    class Meta:
        model = Wishlist
        fields = ['id', 'event', 'created_at']

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "title", "message", "is_read", "type","created_at"]

class PaymentSerializer(serializers.ModelSerializer):
    booking_id = serializers.IntegerField(source="booking.id", read_only=True)
  

    class Meta:
        model = Payment
        fields = [
            "id",
            "booking_id",
            "provider",
            "payment_id",
            "status",
            "amount",
            "receipt_url",
            
        ]
class SupportTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportTicket
        fields = "__all__"
        read_only_fields = ["customer", "status", "created_at", "updated_at"]


class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = "__all__"

class EventRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventRating
        fields = [
            'id', 'event', 'user', 'rating', 'review'
        ]

class BannerSerializer(serializers.ModelSerializer):
    event_id = serializers.IntegerField(source="event.id", read_only=True)
    event_title = serializers.CharField(source="event.title", read_only=True)

    class Meta:
        model = Banner
        fields = ["id", "title", "description", "image", "event_id", "event_title"]
       

        
