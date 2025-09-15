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
            'description',
            'category',
            'location',
            'start_at',
            'end_at',
            'price',
            'total_seats',
            'available_seats',
            'images',
        ]



