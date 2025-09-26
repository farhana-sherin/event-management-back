from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from django.conf import settings


from customer.models import *
from users.models import User
from organizer.models import *





class OrganizerSerializer(ModelSerializer):
    class Meta:
        model =  Organizer
        fields = ['id', 'user']
class EventSerializer(serializers.ModelSerializer):
    is_wishlisted = serializers.SerializerMethodField()
    organizer_email = serializers.EmailField(source="organizer.user.email", read_only=True)

    class Meta:
        model = Event
        fields = "__all__"
        read_only_fields = ["organizer", "qr_code_text", "qr_code_image"]

    def get_is_wishlisted(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            try:
                customer = Customer.objects.get(user=request.user)
                return Wishlist.objects.filter(customer=customer, event=obj).exists()
            except Customer.DoesNotExist:
                return False
        return False