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
        

class EventSerializer(ModelSerializer):
    qr_code_text = serializers.CharField(read_only=True) 
    organizer = serializers.PrimaryKeyRelatedField(read_only=True) 
    class Meta:
        model = Event   
        fields = [
            'id',
            'organizer',
            'title',
            'short_description',
            'description',
            'category',
            'location',
            'start_date',
            'start_time',
            'end_date',
            'end_time',
            'price',
            'images',
            'qr_code_text',
            'is_active',
            'created_at',
            'ticket_count'
                   ]


