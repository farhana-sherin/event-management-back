from rest_framework import serializers
from customer.models import Customer
from users.models import User
from payments.models import *
from api.v1.organizer.serializer import *





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

        
