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
    organizer_email = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    qr_code_image = serializers.SerializerMethodField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        model = Event
        fields = "__all__"
        read_only_fields = ["organizer", "qr_code_text", "qr_code_image"]

    def get_organizer_email(self, obj):
        if obj.organizer and obj.organizer.user:
            return obj.organizer.user.email
        return None
    
    def get_images(self, obj):
        if obj.images:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.images.url)
            # Fallback: construct URL manually if request is not available
            base_url = getattr(settings, 'BASE_URL', 'https://event-management-back-1jat.onrender.com')
            return f"{base_url}{obj.images.url}"
        return None
    
    def get_qr_code_image(self, obj):
        if obj.qr_code_image:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.qr_code_image.url)
            # Fallback: construct URL manually if request is not available
            base_url = getattr(settings, 'BASE_URL', 'https://event-management-back-1jat.onrender.com')
            return f"{base_url}{obj.qr_code_image.url}"
        return None
    
    def get_is_wishlisted(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            try:
                customer = Customer.objects.get(user=request.user)
                return Wishlist.objects.filter(customer=customer, event=obj).exists()
            except Customer.DoesNotExist:
                return False
        return False