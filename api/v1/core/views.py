# api/v1/core/views.py
from django.http import JsonResponse

def home(request):
    return JsonResponse({"message": "Welcome to Room Booking API"})