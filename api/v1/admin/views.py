# api/v1/admin/views.py


from email import message
from ntpath import isabs
from api.v1 import customer
from rest_framework.decorators import api_view, permission_classes,renderer_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from datetime import date
from django.db.models import Sum
import csv
from django.http import HttpResponse
import stripe
from django.views.decorators.csrf import csrf_exempt




from django.contrib.auth import authenticate
from users.models import User
from customer.models import *
from organizer.models import *
from api.v1.organizer.serializer import *
from api.v1.customer.serializer import *
from api.v1.payment.serializer import*
from api.v1.admin.serializer import*

from customer.utils import *
from django.utils import timezone

# Admin Login
@api_view(['POST'])
@permission_classes([AllowAny])
def admin_login(request):
    email = request.data.get("email")
    password = request.data.get("password")
    user = authenticate(email=email, password=password)

    if user and user.is_admin:
        refresh = RefreshToken.for_user(user)

        return Response({
            "status_code": 6000,
            "data": {
                "access": str(refresh.access_token),
                "role": "admin",
                "email": user.email,
            },
            "message": "Admin login successful"
        })
    
    return Response({
        "status_code": 6001,
        "message": "Invalid credentials or not an admin"
    }, status=status.HTTP_401_UNAUTHORIZED)


# Get All Events (for banner creation dropdown)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_events(request):
    if not request.user.is_admin:
        return Response({"status_code": 6003, "message": "Permission denied"}, status=403)
    
    events = Event.objects.all().order_by('-created_at')
    serializer = EventSerializer(events, many=True, context={"request": request})
    return Response({
        "status_code": 6000,
        "data": serializer.data,
        "message": "All events retrieved successfully"
    })


# Get Pending Refunds
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_pending_refunds(request):
    if not request.user.is_admin:
        return Response({"status_code": 6003, "message": "Permission denied"}, status=403)
    
    try:
        # Get bookings where payment status is REFUND_PENDING only
        # Once refunded, bookings should not appear in pending list
        pending_refunds = Booking.objects.filter(
            payment__status="REFUND_PENDING"
        ).select_related('customer__user', 'event', 'payment').order_by('-booking_date')
        
        refund_data = []
        for booking in pending_refunds:
            payment = booking.payment
            # Calculate refund amount (amount - 20 cancellation fee)
            refund_amount = max(float(payment.amount) - 20, 0) if payment else 0
            
            refund_data.append({
                "id": booking.id,
                "customer_name": f"{booking.customer.user.first_name} {booking.customer.user.last_name}".strip() or booking.customer.user.email,
                "customer_email": booking.customer.user.email,
                "event_name": booking.event.title,
                "amount": refund_amount,
                "requested_at": booking.booking_date,
            })
        
        return Response({
            "status_code": 6000,
            "data": refund_data,
            "message": "Pending refunds retrieved successfully"
        })
    except Exception as e:
        return Response({
            "status_code": 6001,
            "message": f"Error fetching refunds: {str(e)}"
        }, status=500)


# Approve Refund
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def approve_refund(request, booking_id):
    if not request.user.is_admin:
        return Response({"status_code": 6003, "message": "Permission denied"}, status=403)
    
    try:
        booking = Booking.objects.get(id=booking_id)
        payment = getattr(booking, "payment", None)
        
        if not payment:
            return Response({
                "status_code": 6001,
                "message": "No payment found for this booking"
            }, status=400)
        
        # Calculate refund amount (same logic as cancel_booking)
        refund_amount = max(float(payment.amount) - 20, 0)
        
        # Check payment status
        if payment.status == "REFUND_PENDING":
            # NEW FLOW: Process Stripe refund now (admin approved!)
            if payment.payment_intent_id:
                try:
                    stripe.Refund.create(
                        payment_intent=payment.payment_intent_id,
                        amount=int(refund_amount * 100)
                    )
                except stripe.error.StripeError as e:
                    return Response({
                        "status_code": 6001,
                        "message": f"Stripe refund failed: {str(e)}"
                    }, status=400)
            
            # Update payment status to REFUNDED
            payment.status = "REFUNDED"
            payment.save()
            message = "Refund approved and processed successfully"
            
        elif payment.status == "REFUNDED":
            # OLD FLOW: Refund already processed, just acknowledge
            message = "Refund already processed (old cancellation)"
        else:
            return Response({
                "status_code": 6001,
                "message": f"Invalid payment status: {payment.status}. Expected REFUND_PENDING or REFUNDED."
            }, status=400)
        
        # Mark booking as cancelled if it has status field
        try:
            booking.status = "CANCELLED"
            booking.save()
        except Exception:
            # Booking model might not have status field yet (before migration)
            pass
        
        # Notify customer
        create_notification(
            customer=booking.customer,
            title="Refund Approved",
            message=f"Your refund of ₹{refund_amount} for '{booking.event.title}' has been approved and processed.",
            organizer=None,
            sender_role="ADMIN"
        )
        
        return Response({
            "status_code": 6000,
            "message": message,
            "refund_amount": refund_amount
        })
        
    except Booking.DoesNotExist:
        return Response({
            "status_code": 6001,
            "message": "Booking not found"
        }, status=404)
    except Exception as e:
        return Response({
            "status_code": 6001,
            "message": f"Error approving refund: {str(e)}"
        }, status=400)


# Reject Refund
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reject_refund(request, booking_id):
    if not request.user.is_admin:
        return Response({"status_code": 6003, "message": "Permission denied"}, status=403)
    
    try:
        booking = Booking.objects.get(id=booking_id)
        payment = getattr(booking, "payment", None)
        
        # Update payment status back to SUCCESS if it was REFUND_PENDING
        if payment and payment.status == "REFUND_PENDING":
            payment.status = "SUCCESS"
            payment.save()
        
        # Update booking status back to CONFIRMED
        try:
            booking.status = "CONFIRMED"
            booking.save()
        except Exception:
            # Booking model might not have status field yet (before migration)
            pass
        
        # Notify customer
        create_notification(
            customer=booking.customer,
            title="Refund Request Rejected",
            message=f"Your refund request for '{booking.event.title}' has been rejected by admin. Your booking is now confirmed.",
            organizer=None,
            sender_role="ADMIN"
        )
        
        return Response({
            "status_code": 6000,
            "message": "Refund request rejected successfully"
        })
        
    except Booking.DoesNotExist:
        return Response({
            "status_code": 6001,
            "message": "Booking not found"
        }, status=404)
    except Exception as e:
        return Response({
            "status_code": 6001,
            "message": f"Error rejecting refund: {str(e)}"
        }, status=400)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_dashboard_summary(request):
    today = timezone.now().date()

    total_customers = Customer.objects.count()
    total_organizers = Organizer.objects.count()
    total_users = total_customers + total_organizers  # Add this
    total_events = Event.objects.count()
    upcoming_events = Event.objects.filter(end_date__gte=today).count()
    total_bookings = Booking.objects.count()
    total_revenue = Payment.objects.filter(status="SUCCESS").aggregate(total=Sum("amount"))["total"] or 0
    # Fix: Payment model doesn't have REFUNDED status, using FAILED for refunded payments
    cancelled_bookings = Booking.objects.filter(payment__status="FAILED").count()

    return Response({
        "status_code": 6000,
        "data": {
            "total_users": total_users,  # Add this
            "total_customers": total_customers,
            "total_organizers": total_organizers,
            "total_events": total_events,
            "upcoming_events": upcoming_events,
            "total_bookings": total_bookings,
            "total_revenue": total_revenue,
            "cancelled_bookings": cancelled_bookings
        },
        "message": "Admin dashboard summary"
    })




@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_list(request):
    
    limit = int(request.query_params.get('limit', 10))
    offset = int(request.query_params.get('offset', 0))
    role = request.query_params.get('role', None)

    
    customers = Customer.objects.select_related('user').all()
    customer_data = [
        {
            "id": c.user.id,
            "name": f"{c.user.first_name} {c.user.last_name}".strip() or c.user.email,
            "email": c.user.email,
            "phone": c.user.phone or "-",
            "role": "customer"
        }
        for c in customers
    ]


    organizers = Organizer.objects.select_related('user').all()
    organizer_data = [
        {
            "id": o.user.id,
            "name": f"{o.user.first_name} {o.user.last_name}".strip() or o.user.email,
            "email": o.user.email,
            "phone": o.user.phone or "-",
            "organization_name": getattr(o, "organization_name", None),
            "role": "organizer"
        }
        for o in organizers
    ]

    all_users = customer_data + organizer_data

    if role in ["customer", "organizer"]:
        all_users = [u for u in all_users if u["role"] == role]

   
    all_users = sorted(all_users, key=lambda x: x["id"], reverse=True)

   
    paginated_users = all_users[offset: offset + limit]

    return Response({
        "status_code": 6000,
        "total_count": len(all_users),
        "users": paginated_users,
        "message": "Successfully retrieved users"
    })



@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def user_delete(request, pk):
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    
    user.delete()
    return Response({"success": "User deleted"}, status=status.HTTP_204_NO_CONTENT)

# EDIT a user
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def user_update(request, pk):
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = UserSerializer(user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admin_bookings(request):
    if not request.user.is_superuser:
        return Response({"status_code": 6001, "message": "Unauthorized"}, status=403)

    bookings = Booking.objects.all()
    status_filter = request.query_params.get("status")
    event_id = request.query_params.get("event")
    customer_id = request.query_params.get("customer")

    # TODO: Uncomment after running migrations to add status field to Booking model
    # if status_filter:
    #     bookings = bookings.filter(status=status_filter.upper())
    if event_id:
        bookings = bookings.filter(event__id=event_id)
    if customer_id:
        bookings = bookings.filter(customer__id=customer_id)

    serializer = AdminBookingSerializer(bookings, many=True, context={"request": request})
    return Response({
        "status_code": 6000,
        "data": serializer.data,
        "message": "Bookings list retrieved"
    })



@api_view(["POST"])
@permission_classes([IsAuthenticated])
def admin_cancel_booking(request, booking_id):
    if not request.user.is_superuser:
        return Response({"status_code": 6001, "message": "Unauthorized"}, status=403)

    try:
        booking = Booking.objects.get(id=booking_id)
        payment = getattr(booking, "payment", None)
        refund_amount = 0

        if payment and payment.status == "SUCCESS":
            refund_amount = max(float(payment.amount) - 20, 0)  
            if payment.payment_intent_id:
                stripe.Refund.create(payment_intent=payment.payment_intent_id, amount=int(refund_amount * 100))

            payment.status = "REFUNDED"
            payment.amount_refunded = refund_amount
            payment.save()

        booking.status = "CANCELLED"
        booking.save()

        return Response({
            "status_code": 6000,
            "message": "Booking cancelled successfully",
            "refund_amount": refund_amount
        })
    except Booking.DoesNotExist:
        return Response({"status_code": 6001, "message": "Booking not found"}, status=404)




@api_view(['GET'])
@permission_classes([IsAuthenticated])

def admin_notifications(request):
    notifications = Notification.objects.all().order_by('-created_at')
    serializer = NotificationSerializer(notifications, many=True)
    return Response(serializer.data)



@api_view(['GET'])
@permission_classes([IsAuthenticated])

def admin_support_tickets(request):
    tickets = SupportTicket.objects.all().order_by('-created_at')
    serializer = SupportTicketSerializer(tickets, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])

def reply_ticket(request, ticket_id):
    ticket = SupportTicket.objects.filter(id=ticket_id).first()
    if not ticket:
        return Response({"error": "Ticket not found"}, status=status.HTTP_404_NOT_FOUND)

    message = request.data.get('message')
    if not message:
        return Response({"error": "Message is required"}, status=status.HTTP_400_BAD_REQUEST)

    reply = TicketReply.objects.create(ticket=ticket, sender=request.user, message=message)
    serializer = TicketReplySerializer(reply)
    return Response(serializer.data, status=status.HTTP_201_CREATED)
    

@csrf_exempt  
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_ticket_status(request, ticket_id):
    # Get the ticket or return 404
    try:
        ticket = SupportTicket.objects.get(id=ticket_id)
    except SupportTicket.DoesNotExist:
        return Response({"error": "Ticket not found"}, status=status.HTTP_404_NOT_FOUND)

  
    status_value = request.data.get('status')
    if not status_value:
        return Response({"error": "Status is required"}, status=status.HTTP_400_BAD_REQUEST)

    valid_statuses = dict(SupportTicket.STATUS_CHOICES).keys()
    if status_value not in valid_statuses:
        return Response({"error": f"Invalid status. Must be one of {list(valid_statuses)}"}, status=status.HTTP_400_BAD_REQUEST)

  
    ticket.status = status_value
    ticket.save()

   
    serializer = SupportTicketSerializer(ticket)
    return Response({
        "message": "Ticket status updated successfully",
        "ticket": serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_all_notifications(request):
    if not request.user.is_admin:
        return Response({"error": "Unauthorized"}, status=403)
    Notification.objects.all().delete()
    return Response({"message": "All notifications deleted"}, status=200)




@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_notification(request):

    if not request.user.is_admin:
        return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

    serializer = SendNotificationSerializer(data=request.data)
    if serializer.is_valid():
        sender_role = serializer.validated_data['sender_role']
        title = serializer.validated_data['title']
        message = serializer.validated_data['message']
        target_group = serializer.validated_data['target_group']

        created_notifications = []

        if target_group == "CUSTOMERS":
            customers = Customer.objects.all()
            for c in customers:
                notif = Notification.objects.create(
                    sender_role=sender_role,
                    customer=c,
                    title=title,
                    message=message
                )
                created_notifications.append(notif.id)

        elif target_group == "ORGANIZERS":
            organizers = Organizer.objects.all()
            for o in organizers:
                notif = Notification.objects.create(
                    sender_role=sender_role,
                    organizer=o,
                    title=title,
                    message=message
                )
                created_notifications.append(notif.id)

        elif target_group == "ALL":
            customers = Customer.objects.all()
            organizers = Organizer.objects.all()
            for c in customers:
                notif = Notification.objects.create(
                    sender_role=sender_role,
                    customer=c,
                    title=title,
                    message=message
                )
                created_notifications.append(notif.id)
            for o in organizers:
                notif = Notification.objects.create(
                    sender_role=sender_role,
                    organizer=o,
                    title=title,
                    message=message
                )
                created_notifications.append(notif.id)

        return Response({
            "message": f"Notifications sent to {len(created_notifications)} recipients ({target_group})",
            "notifications_created": created_notifications
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_all_support_tickets(request):
    SupportTicket.objects.all().delete()  
    return Response({"status_code": 6000, "message": "All support tickets deleted successfully"})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admin_organizer_income(request):
   
    organizers = Organizer.objects.all()
    data = []

    for org in organizers:
        # Get total income
        total_income = Payment.objects.filter(
            booking__event__organizer=org,
            status="SUCCESS"
        ).aggregate(total=Sum("amount"))["total"] or 0
        
        # Get total events
        total_events = Event.objects.filter(organizer=org).count()
        
        # Get total bookings for this organizer's events
        total_bookings = Booking.objects.filter(event__organizer=org).count()

        data.append({
            "organizer_id": org.id,
            "organizer_name": f"{org.user.first_name} {org.user.last_name}".strip() or org.user.email,
            "organizer_email": org.user.email,
            "total_income": total_income,
            "total_events": total_events,
            "total_bookings": total_bookings
        })

    return Response({
        "status_code": 6000,
        "data": data,
        "message": "Organizer incomes retrieved successfully"
    })





@api_view(["POST"])
@permission_classes([IsAuthenticated])
def approve_event(request, pk):
    try:
        event = Event.objects.get(pk=pk)
        event.status = "APPROVED"
        event.is_active = True
        event.save()

    
        organizer = event.organizer
        if organizer:
            create_notification(
                customer=None,
                title="Event Approved",
                message=f"Your event '{event.title}' has been approved by admin.",
                organizer=organizer,
                sender_role="ADMIN"
            )

        return Response({"status_code": 6000, "message": "Event approved"})
    except Event.DoesNotExist:
        return Response({"status_code": 6001, "error": "Event not found"}, status=404)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def deactivate_event(request, pk):
    try:
        event = Event.objects.get(pk=pk)
        event.status = "DEACTIVATED"
        event.is_active = False
        event.save()

        organizer = event.organizer
        if organizer:
            create_notification(
                customer=None,
                title="Event Deactivated",
                message=f"Your event '{event.title}' has been deactivated by admin.",
                organizer=organizer,
                sender_role="ADMIN"
            )

        return Response({"status_code": 6000, "message": "Event deactivated"})
    except Event.DoesNotExist:
        return Response({"status_code": 6001, "error": "Event not found"}, status=404)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cancel_event(request, pk):
    try:
        event = Event.objects.get(pk=pk)
        event.status = "CANCELLED"
        event.is_active = False
        event.save()

        organizer = event.organizer
        if organizer:
            create_notification(
                customer=None,
                title="Event Cancelled",
                message=f"Your event '{event.title}' has been cancelled by admin.",
                organizer=organizer,
                sender_role="ADMIN"
            )

        return Response({"status_code": 6000, "message": "Event cancelled"})
    except Event.DoesNotExist:
        return Response({"status_code": 6001, "error": "Event not found"}, status=404)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def upcoming_events_admin(request):
  
    if not request.user.is_admin:
        return Response({"status_code": 6003, "message": "Permission denied"}, status=403)

    events = Event.objects.filter(start_date__gte=date.today(), status="APPROVED")
    serializer = EventSerializer(events, many=True, context={"request": request})
    return Response({"status_code": 6000, "data": serializer.data})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def past_events_admin(request):
    if not request.user.is_admin:
        return Response({"status_code": 6003, "message": "Permission denied"}, status=403)

    events = Event.objects.filter(end_date__lt=date.today(), status="APPROVED")
    serializer = EventSerializer(events, many=True, context={"request": request})
    return Response({"status_code": 6000, "data": serializer.data})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def cancelled_events_admin(request):
    if not request.user.is_admin:
        return Response({"status_code": 6003, "message": "Permission denied"}, status=403)

    events = Event.objects.filter(status="CANCELLED")
    serializer = EventSerializer(events, many=True, context={"request": request})
    return Response({"status_code": 6000, "data": serializer.data})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def pending_events_admin(request):
    if not request.user.is_admin:
        return Response({"status_code": 6003, "message": "Permission denied"}, status=403)

    events = Event.objects.filter(status="PENDING")
    serializer = EventSerializer(events, many=True, context={"request": request})
    return Response({"status_code": 6000, "data": serializer.data})




@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_banner(request):
    serializer = BannerSerializer(data=request.data, context={"request": request})
    if serializer.is_valid():
        serializer.save()
        return Response({
            "status_code": 6000,
            "data": serializer.data,
            "message": "Banner created successfully"
        })
    return Response({
        "status_code": 6001,
        "errors": serializer.errors,
        "message": "Failed to create banner"
    }, status=400)










