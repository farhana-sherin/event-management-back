from api.v1 import customer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.crypto import get_random_string
from django.conf import settings
import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.shortcuts import get_object_or_404
from users.models import User
from customer.models import *
from organizer.models import *

from api.v1.organizer.serializer import *
from api.v1.customer.serializer import *
from api.v1.payment.serializer import *

from customer.utils import create_notification
from django.utils import timezone

# 1️⃣ Create Booking
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_booking(request):
    data = request.data
    customer = get_object_or_404(Customer, user=request.user)
    event = get_object_or_404(Event, id=data.get("event"))
    tickets_count = int(data.get("tickets_count", 1))
    total_price = event.price * tickets_count

    booking = Booking.objects.create(
        customer=customer,
        event=event,
        tickets_count=tickets_count
    )

    return Response({
        "status": 6000,
        "booking_id": booking.id,
        "total_price": total_price
    })


# 2️⃣ Increment Ticket
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def increment_ticket(request, event_id):
    key = f"user_{request.user.id}_event_{event_id}_tickets"
    tickets = request.session.get(key, 1)
    tickets += 1
    request.session[key] = tickets
    request.session.modified = True

    event = get_object_or_404(Event, id=event_id)
    total_price = event.price * tickets

    return Response({
        "tickets_count": tickets,
        "total_price": total_price
    })


# 3️⃣ Decrement Ticket
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def decrement_ticket(request, event_id):
    key = f"user_{request.user.id}_event_{event_id}_tickets"
    tickets = request.session.get(key, 1)
    if tickets > 1:
        tickets -= 1
    request.session[key] = tickets
    request.session.modified = True

    event = get_object_or_404(Event, id=event_id)
    total_price = event.price * tickets

    return Response({
        "tickets_count": tickets,
        "total_price": total_price
    })


# 4️⃣ Create Stripe Checkout Session
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_checkout_session(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    if booking.customer.user != request.user:
        return Response({"error": "You are not authorized for this booking."}, status=403)

    tickets_count = int(request.data.get("tickets_count", booking.tickets_count))
    total_amount = booking.event.price * tickets_count

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
                    "currency": "inr",
                    "product_data": {
                        "name": booking.event.title,
                        "description": f"Tickets for {booking.event.title}, Qty: {tickets_count}"
                    },
                    "unit_amount": int(booking.event.price * 100),
                },
                "quantity": tickets_count,
            }],
            mode="payment",
            success_url=f"http://localhost:5173/payment/success?booking_id={booking.id}&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url="http://localhost:5173/payment/cancel"
        )

        payment.payment_id = session.id
        payment.payment_intent_id = session.payment_intent 
        payment.amount = total_amount
        payment.save()

        return Response({"sessionId": session.id, "checkout_url": session.url})

    except Exception as e:
        return Response({"error": str(e)}, status=500)


# 5️⃣ Stripe Webhook
@api_view(["POST"])
@permission_classes([AllowAny])
def stripe_webhook(request):
    payload = request.body
    try:
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", None)
        if sig_header:
            event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
        else:
            import json
            event = json.loads(payload)
    except Exception as e:
        return Response({"error": str(e)}, status=400)

    if event.get("type") == "checkout.session.completed":
        session = event["data"]["object"]
        try:
            payment = Payment.objects.get(payment_id=session["id"])
            payment.status = "SUCCESS"
            payment.save()

            booking = payment.booking
            booking.qr_code_text = f"BOOKING:{booking.id}|EVENT:{booking.event.id}|TICKETS:{booking.tickets_count}|EMAIL:{booking.customer.user.email}"
            booking.save()

            # ✅ Send notification
            create_notification(
                customer=booking.customer,
                title="Booking Successful",
                message=f"Your booking for '{booking.event.title}' is confirmed!",
                sender_role="ADMIN"
            )

        except Payment.DoesNotExist:
            pass

    return Response(status=200)


# 6️⃣ Verify Payment
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def verify_payment(request, booking_id, session_id):
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        payment = Payment.objects.get(payment_id=session.id)
        booking = payment.booking

        if session.payment_status == "paid" and payment.status != "SUCCESS":
            payment.status = "SUCCESS"
            payment.save()

            if not booking.qr_code_text:
                booking.qr_code_text = f"BOOKING:{booking.id}|EVENT:{booking.event.title}|TICKETS:{booking.tickets_count}|EMAIL:{booking.customer.user.email}|PRICE:{booking.event.price}"
                booking.save()

            # ✅ Send notification
            create_notification(
                customer=booking.customer,
                title="Booking Successful",
                message=f"Your booking for '{booking.event.title}' is confirmed!",
                sender_role="ADMIN"
            )

        return Response({
            "booking_id": booking.id,
            "payment_id": payment.payment_id,
            "amount": payment.amount,
            "status": payment.status,
            "tickets_count": booking.tickets_count,
            "event": {
                "id": booking.event.id,
                "title": booking.event.title,
                "description": booking.event.description,
                "price": booking.event.price
            },
            "qr_code_text": booking.qr_code_text
        })

    except Payment.DoesNotExist:
        return Response({"error": "Payment record not found"}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=400)
