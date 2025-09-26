from email import message
from ntpath import isabs
from api.v1 import customer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from datetime import date
from datetime import datetime

from django.conf import settings
import stripe
import uuid

from django.contrib.auth import authenticate
from users.models import User
from customer.models import *
from organizer.models import *
from api.v1.organizer.serializer import *
from api.v1.customer.serializer import *
from api.v1.payment.serializer import*
from customer.utils import *
from django.utils import timezone
from api.v1.admin.serializer import BannerSerializer

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
@permission_classes([IsAuthenticated])
def profile(request, id):
    user = request.user

   
    customer = None
    organizer = None
    admin_obj = None

    try:
        customer = Customer.objects.get(user=user)
    except Customer.DoesNotExist:
        pass

    try:
        organizer = Organizer.objects.get(user=user)
    except Organizer.DoesNotExist:
        pass

    try:
        admin_obj = getattr(user, "admin_profile", None)  
    except:
        pass

    # Determine role
    if admin_obj or getattr(user, "is_admin", False):
        role = "admin"
    elif organizer or getattr(user, "is_eventorganizer", False):
        role = "organizer"
    elif customer or getattr(user, "is_customer", False):
        role = "customer"
    else:
        role = "user"

    
    data = {
        "role": role,
        "email": user.email,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone": getattr(user, "phone", None)
    }

    if customer:
        data["customer"] = CustomerSerializer(customer).data
    if organizer:
        data["organizer"] = {"id": organizer.id}  
    if admin_obj:
        data["admin"] = {"id": admin_obj.id}  

    return Response({
        "status_code": 6000,
        "data": data,
        "message": "Profile retrieved successfully"
    })

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile(request,id):
    user = request.user
    customer = Customer.objects.get(user=user,id=id)
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

    today = timezone.now().date()
    events = Event.objects.filter(end_date__gte=today)  

    if keyword:
        events = events.filter(title__icontains=keyword)
    if category:
        events = events.filter(category__icontains=category)
    if start_date and end_date:
        events = events.filter(start_date__range=[start_date, end_date])

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
@permission_classes([IsAuthenticated])
def events_list(request):
    user = request.user

    
    try:
        customer = Customer.objects.get(user=user)
    except Customer.DoesNotExist:
        customer = None  

    category = request.query_params.get("category")

   
    today = timezone.now().date()
    events = Event.objects.filter(end_date__gte=today)

    if category and category != "All":
        events = events.filter(category__iexact=category)

    serializer = EventSerializer(events, many=True, context={"request": request})
    return Response({
        "status_code": 6000,
        "data": serializer.data,
        "message": "Upcoming events list"
    })

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def event_detail_customer(request, id):
    event = Event.objects.get(id=id)
    serializer = EventSerializer(event, context={"request": request})
    return Response({
        "status_code": 6000,
        "data": serializer.data,
        "message": "Event detail"
    })



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def booking_detail(request, booking_id):
    try:
        booking = Booking.objects.get(id=booking_id, customer__user=request.user)
        serializer = BookingDetailSerializer(booking, context={"request": request})
        return Response({
            "status_code": 6000,
            "data": serializer.data,
            "message": "Booking detail"
        })
    except Booking.DoesNotExist:
        return Response({"status_code": 4004, "message": "Booking not found"})





@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cancel_booking(request, booking_id):
    try:
        booking = Booking.objects.get(id=booking_id, customer__user=request.user)
        payment = getattr(booking, "payment", None)
        refund_amount = 0

        if payment and payment.status == "SUCCESS":
          
            if payment.amount is None:
                return Response({"error": "Payment amount not found"}, status=400)

            
            refund_amount = max(float(payment.amount) - 20, 0)

          
            if payment.payment_intent_id:
                stripe.Refund.create(
                    payment_intent=payment.payment_intent_id,
                    amount=int(refund_amount * 100)  
                )

          
            payment.status = "REFUNDED"
            payment.amount_refunded = refund_amount
            payment.save()

      
        booking.status = "CANCELLED"
        booking.save()

       
        create_notification(
            customer=booking.customer,
            title="Booking Cancelled",
            message=f"Your booking for '{booking.event.title}' has been cancelled. Refund Amount: ₹{refund_amount}",
            sender_role="ADMIN"
        )

        return Response({
            "status_code": 6000,
            "message": "Booking cancelled successfully",
            "refund_amount": refund_amount
        })

    except Booking.DoesNotExist:
        return Response({"error": "Booking not found"}, status=404)
    except stripe.error.StripeError as e:
        return Response({"error": f"Stripe error: {str(e)}"}, status=400)
    except Exception as e:
        return Response({"error": str(e)}, status=400)




@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_bookings(request):
    bookings = Booking.objects.filter(customer__user=request.user).select_related("event")
    today = date.today()  

    latest_bookings = []
    past_bookings = []

    for booking in bookings:
        event = booking.event
        serialized = BookingSerializer(booking, context={"request": request}).data
        
    
        serialized["can_review"] = event.start_date < today

        if event.start_date >= today:
            latest_bookings.append(serialized)
        else:
            past_bookings.append(serialized)

    return Response({
        "status_code": 6000,
        "message": "My bookings retrieved successfully",
        "data": {
            "latest_bookings": latest_bookings,
            "past_bookings": past_bookings
        }
    })





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



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def customer_notifications(request):
    try:
        customer = Customer.objects.get(user=request.user)
    except Customer.DoesNotExist:
        return Response({"status_code": 6001, "data": [], "message": "Customer not found"})

    
    notifications = Notification.objects.filter(customer=customer).order_by('-created_at')
    serializer = NotificationSerializer(notifications, many=True)
    return Response({
        "status_code": 6000,
        "data": serializer.data,
        "message": "Customer notifications retrieved successfully"
    })


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
@permission_classes([AllowAny])  
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
    })





@api_view(["GET"])
@permission_classes([AllowAny])
def featured_events(request):
    today = timezone.now().date()

  
    events = Event.objects.filter(
        is_active=True,
        end_date__gte=today  
    ).order_by('start_date')[:6]

    serializer = EventSerializer(events, many=True, context={"request": request})

    return Response(
        {
        "status_code": 6000,
        "data": serializer.data,
        "message": "Featured events list"
    }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def become_organizer(request):
    user = request.user
    if user.is_eventorganizer:
        return Response({"status_code": 6001, "message": "Already an organizer"})
    
    user.is_eventorganizer = True
    user.save()

    Organizer.objects.create(user=user)

    return Response({
        "status_code": 6000,
        "message": "You are now an organizer!"
    })






@api_view(["POST"])
@permission_classes([IsAuthenticated])
def rate_event(request, event_id):
    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        return Response({"message": "Event not found"})


    if event.end_date and event.end_date > timezone.now().date():
        return Response(
            {"status_code": 6001, "message": "You can only review after the event has ended"},
            
        )

    rating_value = request.data.get("rating")
    review = request.data.get("review", "")

    if not rating_value:
        return Response({"message": "Rating is required"}, status=status.HTTP_400_BAD_REQUEST)


    rating_obj, created = EventRating.objects.update_or_create(
        event=event,
        user=request.user,
        defaults={"rating": rating_value, "review": review},
    )

    serializer = EventRatingSerializer(rating_obj)
    return Response({
        "status_code": 6000,
        "message": "Rating created" if created else "Rating updated",
        "data": serializer.data,
    })



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_event_ratings(request, event_id):
    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        return Response({"message": "Event not found"}, status=status.HTTP_404_NOT_FOUND)

    ratings = EventRating.objects.filter(event=event).select_related("user")
    serializer = EventRatingSerializer(ratings, many=True)

    return Response({
        "status_code": 6000,
        "message": "Ratings retrieved successfully",
        "data": serializer.data,
    })