from rest_framework import serializers
from customer.models import Customer
from users.models import User
from payments.models import *
from api.v1.organizer.serializer import *



class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'user']




class WishlistSerializer(serializers.ModelSerializer):
    event = EventSerializer(read_only=True)

    class Meta:
        model = Wishlist
        fields = ['id', 'event', 'created_at']

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "title", "message", "is_read", "created_at"]

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
    image = serializers.ImageField()  # or use SerializerMethodField

    class Meta:
        model = Banner
        fields = ['id', 'title', 'description', 'image']


class BookingDetailSerializer(serializers.ModelSerializer):
    event = EventSerializer(read_only=True)
    amount_paid = serializers.SerializerMethodField()
    payment_status = serializers.SerializerMethodField()
    refund_amount = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            "id",
            "customer",
            "event",
            "tickets_count",
            "booking_date",
            "qr_code_text",
            "amount_paid",
            "payment_status",
            "refund_amount",
        ]

    def get_amount_paid(self, obj):
        if hasattr(obj, "payment") and obj.payment:
            return obj.payment.amount
        return 0

    def get_payment_status(self, obj):
        if hasattr(obj, "payment") and obj.payment:
            return obj.payment.status
        return "PENDING"

    def get_refund_amount(self, obj):
        if hasattr(obj, "payment") and obj.payment:
            return getattr(obj.payment, "amount_refunded", 0)
        return 0

