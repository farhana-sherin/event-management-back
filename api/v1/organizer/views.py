from email import message
from multiprocessing import context
from ntpath import isabs
from api.v1 import customer
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from datetime import date
from django.db.models import Sum, Avg
from django.db.models.functions import TruncWeek
from django.db.models.functions import TruncMonth
from django.db import transaction
from django.db.models.functions import TruncDay
from django.db.models import Avg, Count
from django.utils import timezone
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile
from django.conf import settings
import stripe
import uuid
from organizer.models import *
from organizer.models import Organizer, Event
from customer.models import *
from payments.models import *
from customer.utils import *
from api.v1.organizer.serializer import *
from api.v1.customer.serializer import *

@api_view(['POST'])
@permission_classes([AllowAny])
def register_organizer(request):
    email = request.data.get('email')
    username = request.data.get('username')
    password = request.data.get('password')
    first_name = request.data.get('first_name')
    last_name = request.data.get('last_name')
    phone = request.data.get('phone')

    if User.objects.filter(email=email).exists():
        return Response({
            "status_code": 6001,
            "message": "User already exits"
        })

    user = User.objects.create_user(
        email=email,
        username=username,
        password=password,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
    )
    user.is_eventorganizer = True
    user.save()

    Organizer.objects.create(user=user)

    refresh = RefreshToken.for_user(user)

    return Response({
        "status_code": 6000,
        "data": {
            "access": str(refresh.access_token),
            "role": "organizer"
        },
        "message": "Organizer registration successful"
    })

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    request.user.auth_token.delete()
    return Response({"status_code": 6000, "message": "Organizer logged out successfully"})

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_event(request):
    organizer = Organizer.objects.filter(user=request.user).first()
    if not organizer:
        return Response({
            "status_code": 6001,
            "errors": {"organizer": ["Organizer profile is not found"]}
        }, status=status.HTTP_400_BAD_REQUEST)

    serializer = EventSerializer(data=request.data, context={"request": request})
    if serializer.is_valid():
        with transaction.atomic():
            event = serializer.save(organizer=organizer)

            frontend_base_url = "http://localhost:5173/event/detail"
            qr_code_text = f"{frontend_base_url}/{event.id}"
            event.qr_code_text = qr_code_text

            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_code_text)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")

            buffer = BytesIO()
            img.save(buffer, format="PNG")
            filename = f"EVENT-{event.id}.png"
            file_buffer = ContentFile(buffer.getvalue(), name=filename)
            event.qr_code_image.save(filename, file_buffer)
            event.save(update_fields=["qr_code_text", "qr_code_image"])

        return Response({
            "status_code": 6000,
            "data": EventSerializer(event, context={"request": request}).data,
            "message": "Event created successfully with QR code!"
        })

    return Response({
        "status_code": 6001,
        "errors": serializer.errors
    })

@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def update_event(request, id):
    user = request.user
    try:
        organizer = Organizer.objects.get(user=user)
    except Organizer.DoesNotExist:
        return Response({"status_code": 6001, "message": "Organizer not found"}, status=status.HTTP_404_NOT_FOUND)

    event = Event.objects.filter(id=id, organizer=organizer).first()
    if not event:
        return Response({"status_code": 6001, "message": "Event not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = EventSerializer(event, data=request.data, partial=True, context={"request": request})
    if serializer.is_valid():
        serializer.save()

        bookings = Booking.objects.filter(event=event)
        for booking in bookings:
            create_notification(
                customer=booking.customer,
                title="Event Updated",
                message=f"The event '{event.title}' has been updated.",
            )

        return Response({
            "status_code": 6000,
            "data": serializer.data,
            "message": "Event updated"
        })

    return Response({
        "status_code": 6001,
        "errors": serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_event(request, id):
    user = request.user

    try:
        organizer = Organizer.objects.get(user=user)
    except Organizer.DoesNotExist:
        return Response({"status_code": 6002, "message": "Organizer not found"}, status=status.HTTP_404_NOT_FOUND)

    event = Event.objects.filter(id=id, organizer=organizer).first()
    if not event:
        return Response({"status_code": 6001, "message": "Event not found"}, status=status.HTTP_404_NOT_FOUND)

    bookings = Booking.objects.filter(event=event)
    for booking in bookings:
        create_notification(
            customer=booking.customer,
            title="Event Cancelled",
            message=f"The event '{event.title}' has been deleted. Your payment will be returned soon.",
            organizer=organizer,
        )

    bookings.delete()
    event.delete()

    return Response({"status_code": 6000, "message": "Event deleted and customers notified"})

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_events(request):
    user = request.user
    organizer = Organizer.objects.filter(user=user).first()
    if not organizer:
        return Response({
            "status_code": 6001,
            "data": [],
            "message": "Organizer profile not found"
        })

    events = Event.objects.filter(organizer=organizer)
    serializer = EventSerializer(events, many=True, context={"request": request})
    return Response({
        "status_code": 6000,
        "data": serializer.data,
        "message": "My events"
    })

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def event_detail_organizer(request, id):
    user = request.user
    organizer = Organizer.objects.get(user=user)

    try:
        event = Event.objects.get(id=id, organizer=organizer)
    except Event.DoesNotExist:
        return Response({"status_code": 6001, "message": "Event not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = EventSerializer(event, context={"request": request})
    return Response({"status_code": 6000, "data": serializer.data, "message": "Event detail"})

@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_ticket_status(request, id):
    ticket = SupportTicket.objects.get(id=id)
    status_value = request.data.get("status")

    valid_choices = dict(SupportTicket.STATUS_CHOICES).keys()

    if status_value not in valid_choices:
        return Response({
            "error": "Invalid status",
            "valid_choices": list(valid_choices)
        }, status=status.HTTP_400_BAD_REQUEST)

    ticket.status = status_value
    ticket.save()
    serializer = SupportTicketSerializer(ticket)
    return Response(serializer.data)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_faq(request):
    serializer = FAQSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors)

@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_faq(request, id):
    faq = FAQ.objects.get(id=id)
    serializer = FAQSerializer(faq, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_faq(request, id):
    faq = FAQ.objects.get(id=id)
    faq.delete()
    return Response({"message": "FAQ deleted"}, status=status.HTTP_204_NO_CONTENT)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def organizer_payments(request):
    organizer = Organizer.objects.filter(user=request.user).first()
    if not organizer:
        return Response({"status_code": 6001, "message": "Organizer profile not found"})

    payments = Payment.objects.filter(
        booking__event__organizer=organizer,
        status="SUCCESS"
    )

    serializer = PaymentSerializer(payments, many=True, context={"request": request})
    return Response({
        "status_code": 6000,
        "data": serializer.data,
        "message": "Payments retrieved"
    })

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def cancelled_bookings(request):
    events = Event.objects.filter(organizer__user=request.user)

    cancelled_bookings = Booking.objects.filter(
        event__in=events,
        payment__status__in=["REFUNDED", "FAILED"]
    ).select_related('customer', 'event', 'payment')

    data = []
    for booking in cancelled_bookings:
        data.append({
            "booking_id": booking.id,
            "customer": booking.customer.user.email,
            "event": booking.event.title,
            "tickets_count": booking.tickets_count,
            "refund_status": getattr(booking.payment, 'status', "NOT_ELIGIBLE"),
            "amount": getattr(booking.payment, 'amount', 0),
            "booking_date": booking.booking_date,
        })

    return Response({
        "status_code": 6000,
        "data": data,
        "message": "Cancelled bookings for your events"
    })

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def organizer_dashboard(request):
    user = request.user
    organizer = Organizer.objects.filter(user=user).first()

    if not organizer:
        return Response({
            "status_code": 6001,
            "message": "Organizer profile not found"
        }, status=404)

    today = timezone.now().date()

    total_events = Event.objects.filter(organizer=organizer).count()

    upcoming_events = Event.objects.filter(
        organizer=organizer,
        end_date__gte=today,
        status="APPROVED"
    ).count()

    total_bookings = Booking.objects.filter(
        event__organizer=organizer
    ).count()

    total_revenue = Payment.objects.filter(
        booking__event__organizer=organizer,
        status="SUCCESS"
    ).aggregate(total=Sum("amount"))["total"] or 0

    cancelled_bookings = Booking.objects.filter(
        event__organizer=organizer,
        payment__status="REFUNDED"
    ).count()

    return Response({
        "status_code": 6000,
        "data": {
            "total_events": total_events,
            "upcoming_events": upcoming_events,
            "total_bookings": total_bookings,
            "total_revenue": total_revenue,
            "cancelled_bookings": cancelled_bookings,
        },
        "message": "Organizer dashboard summary"
    })

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def booking_detail(request, booking_id):
    user = request.user
    organizer = Organizer.objects.filter(user=user).first()
    if not organizer:
        return Response({
            "status_code": 6001,
            "message": "Organizer profile not found"
        }, status=404)

    try:
        booking = Booking.objects.select_related('customer', 'payment', 'event').get(id=booking_id, event__organizer=organizer)
    except Booking.DoesNotExist:
        return Response({
            "status_code": 6001,
            "message": "Booking not found or you don't have permission"
        }, status=404)

    data = {
        "booking_id": booking.id,
        "event_title": booking.event.title,
        "event_date": booking.event.start_date,
        "customer_name": f"{booking.customer.user.first_name} {booking.customer.user.last_name}",
        "customer_email": booking.customer.user.email,
        "tickets_count": booking.tickets_count,
        "payment_status": getattr(booking.payment, "status", "PENDING"),
        "amount_paid": getattr(booking.payment, "amount", 0),
        "booking_date": booking.booking_date,
    }

    return Response({
        "status_code": 6000,
        "data": data,
        "message": f"Booking details for {booking.customer.user.email}"
    })

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def organizer_all_bookings(request):
    user = request.user
    organizer = Organizer.objects.filter(user=user).first()
    if not organizer:
        return Response({
            "status_code": 6001,
            "message": "Organizer profile not found"
        }, status=404)

    bookings = Booking.objects.filter(
        event__organizer=organizer
    ).select_related('customer__user', 'event')

    payment_status = request.query_params.get("payment_status")
    event_status = request.query_params.get("event_status")

    today = date.today()

    filtered_data = []
    for booking in bookings:
        payment = getattr(booking, 'payment', None)
        if payment_status and (not payment or payment.status != payment_status):
            continue

        if event_status == "upcoming" and booking.event.end_date < today:
            continue
        elif event_status == "past" and booking.event.end_date >= today:
            continue

        user_obj = booking.customer.user
        customer_name = (
            user_obj.get_full_name().strip()
            or user_obj.username
            or user_obj.email
        )

        filtered_data.append({
            "booking_id": booking.id,
            "event_title": booking.event.title,
            "event_date": booking.event.start_date,
            "customer_name": customer_name,
            "customer_email": user_obj.email,
            "tickets_count": booking.tickets_count,
            "payment_status": payment.status if payment else "PENDING",
            "amount_paid": payment.amount if payment else 0,
            "booking_date": booking.booking_date,
        })

    return Response({
        "status_code": 6000,
        "data": filtered_data,
        "message": "All bookings for your events"
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def event_categories(request):
    categories = [{"key": key, "value": value} for key, value in Event.CATEGORY_CHOICES]

    return Response({
        "status_code": 6000,
        "data": categories,
        "message": "Event categories fetched successfully"
    })

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def organizer_analytics(request):
    organizer = Organizer.objects.get(user=request.user)
    events = Event.objects.filter(organizer=organizer)

    total_revenue = Payment.objects.filter(booking__event__in=events, status="SUCCESS").aggregate(Sum("amount"))["amount__sum"] or 0
    total_bookings = Booking.objects.filter(event__in=events).count()
    payment_success_count = Payment.objects.filter(booking__event__in=events, status="SUCCESS").count()
    payment_failed_count = Payment.objects.filter(booking__event__in=events, status="FAILED").count()

    return Response({
        "total_revenue": total_revenue,
        "total_bookings": total_bookings,
        "payment_success_count": payment_success_count,
        "payment_failed_count": payment_failed_count,
    })

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def upcoming_events(request):
    organizer = Organizer.objects.filter(user=request.user).first()
    if not organizer:
        return Response({"status_code": 6001, "data": [], "message": "Organizer not found"}, status=404)

    events = Event.objects.filter(start_date__gte=date.today(), status="APPROVED", organizer=organizer)
    serializer = EventSerializer(events, many=True, context={"request": request})
    return Response({"status_code": 6000, "data": serializer.data})

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def past_events(request):
    organizer = Organizer.objects.filter(user=request.user).first()
    if not organizer:
        return Response({"status_code": 6001, "data": [], "message": "Organizer not found"}, status=404)

    events = Event.objects.filter(end_date__lt=date.today(), status="APPROVED", organizer=organizer)
    serializer = EventSerializer(events, many=True, context={"request": request})
    return Response({"status_code": 6000, "data": serializer.data})

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def cancelled_events(request):
    organizer = Organizer.objects.filter(user=request.user).first()
    if not organizer:
        return Response({"status_code": 6001, "data": [], "message": "Organizer not found"}, status=404)

    events = Event.objects.filter(status="CANCELLED", organizer=organizer)
    serializer = EventSerializer(events, many=True, context={"request": request})
    return Response({"status_code": 6000, "data": serializer.data})

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def pending_events(request):
    organizer = Organizer.objects.filter(user=request.user).first()
    if not organizer:
        return Response({"status_code": 6001, "data": [], "message": "Organizer not found"}, status=404)

    events = Event.objects.filter(status="PENDING", organizer=organizer)
    serializer = EventSerializer(events, many=True, context={"request": request})
    return Response({"status_code": 6000, "data": serializer.data, "message": "Pending events"})



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def revenue_by_period(request):
 
    if request.user.is_superuser:
        payments = Payment.objects.filter(status="SUCCESS")
    else:
        organizer = Organizer.objects.filter(user=request.user).first()
        if not organizer:
            return Response({"status_code": 6001, "message": "Organizer profile not found"}, status=404)
        payments = Payment.objects.filter(
            booking__event__organizer=organizer,
            status="SUCCESS"
        )

    revenue_by_day = payments.annotate(period=TruncDay("payment_date"))\
        .values("period").annotate(total=Sum("amount")).order_by("period")

    revenue_by_week = payments.annotate(period=TruncWeek("payment_date"))\
        .values("period").annotate(total=Sum("amount")).order_by("period")

    revenue_by_month = payments.annotate(period=TruncMonth("payment_date"))\
        .values("period").annotate(total=Sum("amount")).order_by("period")

    return Response({
        "status_code": 6000,
        "data": {
            "day": list(revenue_by_day),
            "week": list(revenue_by_week),
            "month": list(revenue_by_month),
        },
        "message": "Revenue analytics grouped by period"
    })



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def revenue_by_category(request):
    if request.user.is_superuser:
        data = Payment.objects.filter(status="SUCCESS")\
            .values("booking__event__category")\
            .annotate(revenue=Sum("amount"))
    else:
        organizer = Organizer.objects.filter(user=request.user).first()
        if not organizer:
            return Response({"status_code": 6001, "message": "Organizer not found"}, status=404)
        data = Payment.objects.filter(
            booking__event__organizer=organizer,
            status="SUCCESS"
        ).values("booking__event__category").annotate(revenue=Sum("amount"))

    formatted = [
        {"category": item["booking__event__category"], "revenue": item["revenue"]}
        for item in data
    ]

    return Response({"status_code": 6000, "data": formatted, "message": "Revenue by category"})



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def tickets_sold_trends(request):
    period = request.query_params.get("period", "day")

    if request.user.is_superuser:
        queryset = Booking.objects.filter(payment__status="SUCCESS")
    else:
        organizer = Organizer.objects.filter(user=request.user).first()
        if not organizer:
            return Response({"status_code": 6001, "message": "Organizer not found"}, status=404)
        queryset = Booking.objects.filter(event__organizer=organizer, payment__status="SUCCESS")

    if period == "day":
        data = queryset.values("booking_date__date")\
            .annotate(tickets_sold=Sum("tickets_count"))\
            .order_by("booking_date__date")
    elif period == "week":
        data = queryset.annotate(week=TruncWeek("booking_date"))\
            .values("week").annotate(tickets_sold=Sum("tickets_count"))\
            .order_by("week")
    elif period == "month":
        data = queryset.annotate(month=TruncMonth("booking_date"))\
            .values("month").annotate(tickets_sold=Sum("tickets_count"))\
            .order_by("month")
    else:
        return Response({"status_code": 6001, "message": "Invalid period"}, status=400)

    return Response({"status_code": 6000, "data": list(data), "message": "Tickets sold trends"})



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def organizer_notifications(request):
    try:
        organizer = Organizer.objects.get(user=request.user)
    except Organizer.DoesNotExist:
        return Response({"status_code": 6001, "data": [], "message": "Organizer not found"}, status=404)

    # Filter notifications sent to this organizer
    notifications = Notification.objects.filter(organizer=organizer).order_by('-created_at')
    serializer = NotificationSerializer(notifications, many=True)
    
    return Response({
        "status_code": 6000,
        "data": serializer.data,
        "message": "Notifications for organizer retrieved successfully"
    })






@api_view(['GET'])
@permission_classes([IsAuthenticated])
def organizer_event_ratings(request):
    try:
        organizer = Organizer.objects.get(user=request.user)

    
        events = Event.objects.filter(organizer=organizer, end_date__lt=timezone.now())

        data = []
        for event in events:
            ratings_qs = EventRating.objects.filter(event=event)
            avg_rating = ratings_qs.aggregate(avg=Avg('rating'))['avg'] or 0
            total_ratings = ratings_qs.count()

            reviews = EventRatingSerializer(ratings_qs, many=True).data

            data.append({
                "event_id": event.id,
                "title": event.title,
                "avg_rating": avg_rating,
                "total_ratings": total_ratings,
                "reviews": reviews,
            })

        return Response({
            "status_code": 6000,
            "message": "Organizer past event ratings fetched successfully",
            "data": data
        })

    except Organizer.DoesNotExist:
        return Response({"status_code": 4001, "message": "Organizer not found", "data": []})