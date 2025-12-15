from rest_framework import serializers
from customer.models import Customer
from users.models import User
from payments.models import *
from api.v1.organizer.serializer import *



class CustomerSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = Customer
        fields = ['id', 'user_id', 'user_email']




class WishlistSerializer(serializers.ModelSerializer):
    event = EventSerializer(read_only=True)

    class Meta:
        model = Wishlist
        fields = ['id', 'event', 'created_at']

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'sender_role', 'title', 'message', 'is_read', 'created_at', 'customer', 'organizer']

class PaymentSerializer(serializers.ModelSerializer):
    booking_id = serializers.IntegerField(source="booking.id", read_only=True)
    customer = serializers.SerializerMethodField()  # Customer info
    event = serializers.SerializerMethodField()     # Event info
    created_at = serializers.DateTimeField(source="payment_date", read_only=True)  # For chart

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
            "customer",
            "event",
            "created_at",
        ]

    def get_customer(self, obj):
        if obj.booking and obj.booking.customer:
            customer = obj.booking.customer
            return {
                "id": customer.id,
                "name": customer.user.get_full_name(),
                "email": customer.user.email,
                "phone": getattr(customer, "phone", ""),
            }
        return None

    def get_event(self, obj):
        if obj.booking and obj.booking.event:
            event = obj.booking.event
            return {
                "id": event.id,
                "title": event.title,
                "category": event.category,
                "price": event.price,
                "start_date": event.start_date,
                "end_date": event.end_date,
                "start_time": event.start_time,
                "end_time": event.end_time,
            }
        return None


class TicketReplySerializer(serializers.ModelSerializer):
    sender_email = serializers.SerializerMethodField()
    sender_role = serializers.SerializerMethodField()

    class Meta:
        model = TicketReply
        fields = ['id', 'ticket', 'sender', 'sender_email', 'sender_role', 'message', 'created_at']

    def get_sender_email(self, obj):
        return obj.sender.email if obj.sender else "Unknown"
    
    def get_sender_role(self, obj):
        if obj.sender.is_admin:
            return "Admin"
        elif obj.sender.is_customer:
            return "Customer"
        return "User"


class SupportTicketSerializer(serializers.ModelSerializer):
    replies = TicketReplySerializer(many=True, read_only=True)
    
    class Meta:
        model = SupportTicket
        fields = "__all__"
        read_only_fields = ["customer", "status", "created_at", "updated_at"]


class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = "__all__"

class EventRatingSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = EventRating
        fields = [
            'id', 'event', 'user', 'user_email', 'rating', 'review'
        ]


class BookingDetailSerializer(serializers.ModelSerializer):
    customer_email = serializers.CharField(source='customer.user.email', read_only=True)
    event = EventSerializer(read_only=True)
    amount_paid = serializers.SerializerMethodField()
    payment_status = serializers.SerializerMethodField()
    refund_amount = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            "id",
            "customer",
             "customer_email",
            "event",
            "tickets_count",
            "booking_date",
            "qr_code_text",
            "amount_paid",
            "payment_status",
            "refund_amount",
        ]

    def get_latest_payment(self, obj):
       
        return Payment.objects.filter(booking=obj).order_by("-payment_date").first()

    def get_amount_paid(self, obj):
        payment = self.get_latest_payment(obj)
        return payment.amount if payment else 0

    def get_payment_status(self, obj):
        payment = self.get_latest_payment(obj)
        return payment.status if payment else "PENDING"

    def get_refund_amount(self, obj):
        payment = self.get_latest_payment(obj)
        return getattr(payment, "amount_refunded", 0) if payment else 0