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
    class Meta:
        model = Event   
        fields = [
            'id',
            'title',
            'short_description',  # Added short_description field
            'description',
            'category',
            'location',
            'start_date',  # Change from start_at to start_date
            'start_time',  # Change from start_at to start_time
            'end_date',    # Change from end_at to end_date
            'end_time',    # Change from end_at to end_time
            'price',
            'total_seats',
            'available_seats',
            'images',
            'is_active',   # Add is_active if needed
        ]



