from api.v1 import customer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.crypto import get_random_string
from django.conf import settings
import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


from django.contrib.auth import authenticate ,login as auth_login, logout as auth_logout
from django.shortcuts import get_object_or_404
from users.models import User
from customer.models import *
from organizer.models import*

from api.v1.organizer.serializer import *
from api.v1.customer.serializer import *
from api.v1.payment.serializer import *








# 1. Create Booking
# 1. Create Booking
# views.py



@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_booking(request):
    data = request.data

    # 1️⃣ Get the customer linked to the logged-in user
    customer = get_object_or_404(Customer, user=request.user)

    # 2️⃣ Get the event
    event = get_object_or_404(Event, id=data.get("event"))

    # 3️⃣ Tickets and total price
    tickets_count = int(data.get("tickets_count", 1))
    total_price = event.price * tickets_count

    # 4️⃣ Create booking
    booking = Booking.objects.create(
        customer=customer,
        event=event,
        tickets_count=tickets_count
        # qr_code_text can stay blank for now
    )

    # 5️⃣ Return response
    return Response({
        "status": 6000,
        "booking_id": booking.id,
        "total_price": total_price
    })


# Increment Ticket by event
# Increment ticket (update quantity)
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def increment_ticket(request, event_id):
    try:
        key = f"user_{request.user.id}_event_{event_id}_tickets"
        tickets = request.session.get(key, 1)
        tickets += 1
        request.session[key] = tickets
        request.session.modified = True

        event = Event.objects.get(id=event_id)
        total_price = event.price * tickets

        return Response({
            "tickets_count": tickets,
            "total_price": total_price
        })
    except Event.DoesNotExist:
        return Response({"error": "Event not found"}, status=404)

# Decrement ticket
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def decrement_ticket(request, event_id):
    try:
        key = f"user_{request.user.id}_event_{event_id}_tickets"
        tickets = request.session.get(key, 1)
        if tickets > 1:
            tickets -= 1
        request.session[key] = tickets
        request.session.modified = True

        event = Event.objects.get(id=event_id)
        total_price = event.price * tickets

        return Response({
            "tickets_count": tickets,
            "total_price": total_price
        })
    except Event.DoesNotExist:
        return Response({"error": "Event not found"}, status=404)

# 2. Create Stripe Checkout Session

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_checkout_session(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    # Ensure only the customer who owns the booking can create a checkout session
    if booking.customer.user != request.user:
        return Response({"error": "You are not authorized for this booking."}, status=403)

    total_amount = booking.event.price * booking.tickets_count  # calculate total dynamically

    # Create Payment if it doesn't exist
    payment, created = Payment.objects.get_or_create(
        booking=booking,
        defaults={
            "provider": "Stripe",
            "payment_id": "",
            "amount": total_amount,
            "status": "PENDING"
        }
    )

    try:
        session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": f"{booking.event.title} - {booking.tickets_count} Ticket(s)",
                            "description": f"Tickets for {booking.event.title}, Qty: {booking.tickets_count}"
                        },
                        "unit_amount": int(booking.event.price * 100),
                    },
                    "quantity": 1,  # keep quantity 1 since we included ticket count in the name
                }],
                mode="payment",
                success_url=f"http://localhost:3000/payment-success?booking_id={booking.id}&session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url="http://localhost:3000/payment-cancel",
            )

        payment.payment_id = session.id
        payment.save()

        return Response({"sessionId": session.id, "checkout_url": session.url})

    except Exception as e:
        return Response({"error": str(e)}, status=500)



@api_view(["POST"])
@permission_classes([IsAuthenticated])
def stripe_webhook(request):
    payload = request.body

    # For testing in Postman only
    try:
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", None)
        if sig_header:
            event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
        else:
            # Skip signature check for manual testing
            import json
            event = json.loads(payload)
    except Exception as e:
        return Response({"error": str(e)}, status=400)

    # Process the event
    if event.get("type") == "checkout.session.completed":
        session = event["data"]["object"]
        try:
            payment = Payment.objects.get(payment_id=session["id"])
            payment.status = "SUCCESS"
            payment.save()

            booking = payment.booking
            booking.qr_code_text = f"BOOKING:{booking.id}|EVENT:{booking.event.id}|TICKETS:{booking.tickets_count}|EMAIL:{booking.customer.user.email}"
            booking.save()
        except Payment.DoesNotExist:
            pass

    return Response(status=200)