from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from datetime import date

from django.conf import settings
import stripe
import uuid

from django.contrib.auth import authenticate
from users.models import User
from customer.models import *
from organizer.models import *
from api.v1.organizer.serializer import *
from api.v1.customer.serializer import *
from customer.utils import *
from django.utils import timezone

stripe.api_key = settings.STRIPE_SECRET_KEY



@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    email = request.data.get("email")
    password = request.data.get("password")
    user = authenticate(email=email, password=password)

    if user:
        refresh = RefreshToken.for_user(user)

        if user.is_admin:
            role = "admin"
        elif user.is_eventorganizer:
            role = "organizer"
        elif user.is_customer:
            role = "customer"
        else:
            role = "unknown"

        return Response({
            "status_code": 6000,
            "data": {
                "access": str(refresh.access_token),
                "role": role,
                "email": user.email,
            },
            "message": "Login successful"
        })
    return Response({
        "status_code": 6001,
        "message": "Invalid credentials"
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    email = request.data.get('email')
    username = request.data.get('username')
    password = request.data.get('password')
    first_name = request.data.get('first_name')
    last_name = request.data.get('last_name')
    phone = request.data.get('phone')

    if User.objects.filter(email=email).exists():
        return Response({
            "status_code": 6001,
            "data": {},
            "message": "User already exists"
        })

    user = User.objects.create_user(
        email=email,
        username=username,
        password=password,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
    )
    user.is_customer = True
    user.save()

    Customer.objects.create(user=user)
    refresh = RefreshToken.for_user(user)

    return Response({
        "status_code": 6000,
        "data": {
            "access": str(refresh.access_token),
            "role": "customer",
            "email": user.email
        },
        "message": "Customer registration successful"
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def profile(request):
    user = request.user
    customer = Customer.objects.get(user=user)
    return Response({
        "status_code": 6000,
        "data": {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "email": user.email,
            "phone": user.phone
        },
        "message": "Profile retrieved successfully"
    })


@api_view(['PUT'])
@permission_classes([AllowAny])
def update_profile(request):
    user = request.user
    user.first_name = request.data.get('first_name', user.first_name)
    user.last_name = request.data.get('last_name', user.last_name)
    user.username = request.data.get('username', user.username)
    user.email = request.data.get('email', user.email)
    user.phone = request.data.get('phone', user.phone)
    user.save()
    return Response({
        "status_code": 6000,
        "data": {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "email": user.email,
            "phone": user.phone
        },
        "message": "Profile updated successfully"
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def search_events(request):
    keyword = request.data.get("keyword", "")
    category = request.data.get("category", "")
    start_date = request.data.get("start_date")
    end_date = request.data.get("end_date")

    events = Event.objects.all()
    if keyword:
        events = events.filter(title__icontains=keyword)
    if category:
        events = events.filter(category__icontains=category)
    if start_date and end_date:
        events = events.filter(start_at__date__range=[start_date, end_date])

    serializer = EventSerializer(events, many=True, context={"request": request})
    return Response({
        "status_code": 6000,
        "data": serializer.data,
        "message": "Search results retrieved successfully"
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    request.user.auth_token.delete()
    return Response({"status_code": 6000, "message": "Logged out successfully"})




@api_view(["GET"])
@permission_classes([AllowAny])
def events_list(request):
    events = Event.objects.all()
    serializer = EventSerializer(events, many=True, context={"request": request})
    return Response({
        "status_code": 6000,
        "data": serializer.data,
        "message": "Events list"
    })

@api_view(["GET"])
@permission_classes([AllowAny])
def event_detail_customer(request, id):
    event = Event.objects.get(id=id)
    serializer = EventSerializer(event, context={"request": request})
    return Response({
        "status_code": 6000,
        "data": serializer.data,
        "message": "Event detail"
    })



@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_booking(request, id):
    customer = Customer.objects.get(user=request.user)
    event = Event.objects.get(id=id)

    tickets_count = request.data.get("tickets_count")
    if not tickets_count:
        return Response({"status_code": 6001, "message": "tickets_count is required"})

    tickets_count = int(tickets_count)
    total_amount = tickets_count * event.price
    qr_code = str(uuid.uuid4())

    booking = Booking.objects.create(
        customer=customer,
        event=event,
        tickets_count=tickets_count,
        total_amount=total_amount,
        status="PENDING",
        qr_code_text=qr_code,
    )

    create_notification(
        customer,
        "Booking Created",
        f"Your booking for '{event.title}' has been created with {tickets_count} tickets. Pending payment.",
        sender_role="ADMIN" 
    )



    serializer = BookingSerializer(booking, context={"request": request})
    return Response({"status_code": 6000, "data": serializer.data, "message": "Booking created"})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cancel_booking(request, id):
    booking = Booking.objects.get(id=id, customer__user=request.user)
    booking.status = "CANCELLED"
    booking.save()

    create_notification(
        booking.customer,
        "Booking Cancelled",
        f"Your booking for '{booking.event.title}' has been cancelled.",
        sender_role="ADMIN"
    )

    return Response({"status_code": 6000, "message": "Booking cancelled"})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_bookings(request):
    bookings = Booking.objects.filter(customer__user=request.user)
    serializer = BookingSerializer(bookings, many=True, context={"request": request})
    return Response({"status_code": 6000, "data": serializer.data, "message": "My bookings"})




@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_to_wishlist(request, id):
    customer = Customer.objects.get(user=request.user)
    event = Event.objects.get(id=id)
    wishlist, created = Wishlist.objects.get_or_create(customer=customer, event=event)
    serializer = WishlistSerializer(wishlist, context={"request": request})
    return Response({"status_code": 6000, "data": serializer.data, "message": "Added to wishlist"})


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def remove_from_wishlist(request, id):
    customer = Customer.objects.get(user=request.user)
    Wishlist.objects.filter(customer=customer, event__id=id).delete()
    return Response({"status_code": 6000, "message": "Removed from wishlist"})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_wishlist(request):
    customer = Customer.objects.get(user=request.user)
    wishlist = Wishlist.objects.filter(customer=customer)
    serializer = WishlistSerializer(wishlist, many=True, context={"request": request})
    return Response({"status_code": 6000, "data": serializer.data, "message": "My wishlist"})



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_notifications(request):
    customer = Customer.objects.get(user=request.user)
    notifications = Notification.objects.filter(customer=customer)
    serializer = NotificationSerializer(notifications, many=True)
    return Response({"status_code": 6000, "data": serializer.data, "message": "Notifications retrieved successfully"})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def notification_detail(request, id):
    customer = Customer.objects.get(user=request.user)
    notification = Notification.objects.filter(id=id, customer=customer).first()

    if not notification:
        return Response({"status_code": 6001, "message": "Notification not found"})

    return Response({
        "status_code": 6000,
        "data": {
            "id": notification.id,
            "title": notification.title,
            "message": notification.message,
            "is_read": notification.is_read,
            "created_at": notification.created_at,
        }
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_all_notifications_read(request):
    customer = Customer.objects.get(user=request.user)
    Notification.objects.filter(customer=customer, is_read=False).update(is_read=True)
    return Response({"status_code": 6000, "message": "All notifications marked as read"})

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def unread_notifications_count(request):
    customer = Customer.objects.get(user=request.user)
    count = Notification.objects.filter(customer=customer, is_read=False).count()
    return Response({"status_code": 6000, "unread_count": count})

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_notification_read(request, id):
    customer = Customer.objects.get(user=request.user)
    notification = Notification.objects.get(id=id, customer=customer)
    notification.is_read = True
    notification.save()
    return Response({"status_code": 6000, "message": "Notification marked as read"})



@api_view(['GET'])
@permission_classes([AllowAny])
def explore_categories(request):
   
    all_categories = []

  
    for category_key, category_name in Event.CATEGORY_CHOICES:
        
        events = Event.objects.filter(category=category_key, is_active=True)
        context={
            "request": request
        }

        serializer = EventSerializer(events, many=True, context=context)

        all_categories.append({
            "category": category_key,
            "events": serializer.data
        })

 
    return Response({
        "status": "success",
        "data": all_categories
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def past_events(request):
 
    customer = Customer.objects.get(user=request.user)


    bookings = Booking.objects.filter(customer=customer)

    # Make a list of events from the bookings
    events = []
    for booking in bookings:
        if booking.event.end_at < timezone.now():   
            events.append(booking.event)
        
        context={
            "request": request
        }

 
    serializer = EventSerializer(events, many=True, context=context)
    return Response({
        "status": "success",
        "data": serializer.data
    })





# ✅ Customer - Create Ticket
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_ticket(request):
    customer = Customer.objects.get(user=request.user)
    subject = request.data.get("subject")
    message = request.data.get("message")

    if not subject or not message:
        return Response(
            {"status_code": 6001, "message": "Subject and message are required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    ticket = SupportTicket.objects.create(
        customer=customer,
        subject=subject,
        message=message
    )
    serializer = SupportTicketSerializer(ticket, context={"request": request})

    return Response({
        "status_code": 6000,
        "data": serializer.data,
        "message": "Support ticket created"
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_tickets(request):
    customer = Customer.objects.get(user=request.user)
    tickets = SupportTicket.objects.filter(customer=customer)
    serializer = SupportTicketSerializer(tickets, many=True)
    return Response(serializer.data)





@api_view(["GET"])
def list_faqs(request):
    faqs = FAQ.objects.all()
    serializer = FAQSerializer(faqs, many=True)
    return Response(serializer.data)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def rating_event(request, id):
    event = Event.objects.get(id=id)
    ratings = event.ratings.all()

    
    serializer = EventRatingSerializer(ratings, many=True)

    if ratings.exists():
        total = sum(r.rating for r in ratings)
        average = round(total / ratings.count(), 2)
    else:
        average = 0

    return Response({
        "status_code": 6000,
        "data": {
            "event": event.title,
            "average_rating": average,
            "total_ratings": ratings.count(),
            "ratings": serializer.data
        },
        "message": "Event ratings fetched successfully"
    })

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def rate_event(request, id):
    event = Event.objects.get(id=id)

    rating = EventRating(
        event=event,
        user=request.user,
        rating=request.data.get("rating"),
        review=request.data.get("review", "")
    )
    rating.save()

    serializer = EventRatingSerializer(rating)

    return Response({
        "status_code": 6000,
        "data": serializer.data,
        "message": "Rating submitted successfully"
    })
    
@api_view(["GET"])
@permission_classes([AllowAny])  # customers can see banners without login
def banner_list(request):
    banners = Banner.objects.all().order_by("-created_at")
    serializer = BannerSerializer(banners, many=True, context={"request": request})
    return Response({
        "status_code": 6000,
        "data": serializer.data,
        "message": "Banner list"
    })



@api_view(["GET"])
@permission_classes([AllowAny])
def upcoming_events(request):
   
    today = date.today()
    events = Event.objects.filter(start_date__gte=today, is_active=True).order_by('start_date')

   

    # Optional: limit number of events (e.g., 3 for index)
    limit = request.query_params.get('limit')
    if limit:
        try:
            limit = int(limit)
            events = events[:limit]
        except ValueError:
            pass 

    serializer = EventSerializer(events, many=True, context={"request": request})
    return Response({
        "status_code": 6000,
        "data": serializer.data,
        "message": "Upcoming events fetched successfully"
    }, status=status.HTTP_200_OK)



@api_view(["GET"])
@permission_classes([AllowAny])
def featured_events(request):
    # Fetch only active events, limit to 3
    events = Event.objects.filter(is_active=True).order_by('-id')[:6]
    serializer = EventSerializer(events, many=True, context={"request": request})
    return Response({
        "status_code": 6000,
        "data": serializer.data,
        "message": "Featured events list"
    })