from rest_framework import serializers
from customer.models import Customer
from users.models import User
from payments.models import *
from api.v1.organizer.serializer import *





class BookingSerializer(serializers.ModelSerializer):
    event = EventSerializer(read_only=True)
    

    class Meta:
        model = Booking
        fields = "__all__"

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = "__all__"

        
