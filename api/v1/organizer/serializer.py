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
    images = serializers.FileField(required=False, allow_null=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        model = Event
        fields = "__all__"
        read_only_fields = ["organizer", "qr_code_text", "qr_code_image"]

    def get_organizer_email(self, obj):
        if obj.organizer and obj.organizer.user:
            return obj.organizer.user.email
        return None
    
    def to_representation(self, instance):
        """Override to return absolute URLs for images"""
        representation = super().to_representation(instance)
        
        # Convert images to absolute URL
        if instance.images:
            request = self.context.get("request")
            if request:
                representation['images'] = request.build_absolute_uri(instance.images.url)
            else:
                base_url = getattr(settings, 'BASE_URL', 'https://event-management-back-1jat.onrender.com')
                representation['images'] = f"{base_url}{instance.images.url}"
        else:
            representation['images'] = None
        
        # Convert qr_code_image to absolute URL
        if instance.qr_code_image:
            request = self.context.get("request")
            if request:
                representation['qr_code_image'] = request.build_absolute_uri(instance.qr_code_image.url)
            else:
                base_url = getattr(settings, 'BASE_URL', 'https://event-management-back-1jat.onrender.com')
                representation['qr_code_image'] = f"{base_url}{instance.qr_code_image.url}"
        else:
            representation['qr_code_image'] = None
        
        return representation
    
    def get_is_wishlisted(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            try:
                customer = Customer.objects.get(user=request.user)
                return Wishlist.objects.filter(customer=customer, event=obj).exists()
            except Customer.DoesNotExist:
                return False
        return False