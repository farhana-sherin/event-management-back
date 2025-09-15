from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.crypto import get_random_string
from django.conf import settings
import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


from django.contrib.auth import authenticate ,login as auth_login, logout as auth_logout
from users.models import User
from customer.models import *
from organizer.models import*
from api.v1.organizer.serializer import *
from api.v1.customer.serializer import *
from api.v1.payment.serializer import *









@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_payment(request,id):
   
    user = request.user
    booking = Booking.objects.filter(id=id, user=user).first()
    if not booking:
        return Response({"status_code": 6001, "message": "Booking not found"})

    if booking.status == "PAID":
        payment = Payment.objects.filter(booking=booking).first()
        serializer = PaymentSerializer(payment, context={"request": request})
        
        return Response({"status_code": 6002, "message": "Booking already paid"})

    amount = int(booking.total_amount * 100)  

    payment_intent = stripe.PaymentIntent.create(
        amount=amount,
        currency='inr',
        metadata={
            "booking_id": booking.id,
            "customer_email": user.email
        },
    )

    return Response({
        "status_code": 6000,
        "data": {
            "client_secret": payment_intent.client_secret,
                "payment_intent_id": payment_intent.id,
                "amount": booking.total_amount
        },
        "message": "Payment initiated successfully"
    })

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def confirm_payment(request, id):
    user = request.user
    booking = Booking.objects.filter(id=id, customer__user=user).first()

    if not booking:
        return Response({
            "status_code": 6001, 
            "data": {},
            "message": "Booking not found"
        })

    if booking.status == "PAID":
        payment = Payment.objects.filter(booking=booking).first()
        serializer = PaymentSerializer(payment, context={"request": request})
        return Response({
            "status_code": 6002, 
            "data": serializer.data if payment else {},
            "message": "Booking already paid"
        })

 
    booking.status = "PAID"
    booking.save()

   
    payment, created = Payment.objects.update_or_create(
        booking=booking,
        defaults={
            "customer": booking.customer,
            "provider": "Stripe",
            "payment_id": f"STRIPE-{booking.id}-{booking.qr_code}",
            "status": "SUCCESS",
            "amount": booking.total_amount,
            "receipt_url": "",
        }
    )

    serializer = PaymentSerializer(payment, context={"request": request})

    return Response({
        "status_code": 6000,
        "data": serializer.data,
        "message": "Payment confirmed and booking marked as PAID"
    })