from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken 

from organizer.models import *

from customer.models import *
from payments.models import*

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
            "errors": {"organizer": ["Organizer profile not found for this user"]}
        }, status=status.HTTP_400_BAD_REQUEST)

    serializer = EventSerializer(data=request.data, context={"request": request})
    if serializer.is_valid():
        event = serializer.save(organizer=organizer) 
        return Response({
            "status_code": 6000,
            "data": serializer.data,
            "message": "Event created"
        })

    return Response({
        "status_code": 6001,
        "errors": serializer.errors
    })


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_event(request, id):

    user = request.user
    organizer = Organizer.objects.get(user=user)
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
                type="EVENT"
            )

        return Response({
            "status_code": 6000,
            "data": serializer.data,
            "message": "Event updated"
        })

    return Response({
        "status_code": 6001,
        "errors": serializer.errors
    })


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_event(request, id):
    user = request.user
    organizer = Organizer.objects.get(user=user)
    event = Event.objects.filter(id=id, organizer=organizer).first()

   
    if not event:
        return Response({"status_code": 6001, "message": "Event not found"}, status=status.HTTP_404_NOT_FOUND)

   
    bookings = Booking.objects.filter(event=event)
    for booking in bookings:
        create_notification(
            customer=booking.customer,
            title="Event Cancelled",
            message=f"The event '{event.title}' has been cancelled.",
            organizer=organizer,
        )

    event.delete()
    return Response({"status_code": 6000, "message": "Event deleted"})



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
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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

