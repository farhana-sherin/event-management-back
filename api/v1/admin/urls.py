from django.urls import path

from api.v1.admin import views
app_name = 'admin_api'



urlpatterns = [
    path('admin/login/', views.admin_login, name='admin_login'),
    path('admin/dashboard-summary/', views.admin_dashboard_summary,name='admin_dashboard_summary'),
    path('admin/users/', views.user_list, name='user-list'),          # GET all users
    path('admin/users/<int:pk>/', views.user_delete, name='user-delete'), # DELETE
    path('admin/users/<int:pk>/edit/', views.user_update, name='user-update'),
    path('admin/bookings/', views.admin_bookings, name='admin-bookings'), 
    path('admin/cancelled/<int:booking_id>/', views.admin_cancel_booking, name='admin-bookings'), 
    path('admin/notifications/', views.admin_notifications, name='admin_notifications'),
    path('admin/support-tickets/', views.admin_support_tickets, name='admin_support_tickets'),
    path('admin/support-tickets/<int:ticket_id>/reply/', views.reply_ticket, name='reply_ticket'),
    path('admin/support-tickets/<int:ticket_id>/update-status/', views.update_ticket_status, name='update_ticket_status'),
    path('admin/send-notification/', views.send_notification, name='send_notification'),
    path('admin/delete/notification/', views.delete_all_notifications, name='delete-notification'),
    path("admin/support-tickets/delete-all/", views.delete_all_support_tickets, name="delete-supportList"),
    path("admin/organizer/income/", views.admin_organizer_income, name="organizer-income"),
    path("admin/events/<int:pk>/approve/", views.approve_event),
    path("admin/events/<int:pk>/deactivate/", views.deactivate_event),
    path("admin/events/<int:pk>/cancel/", views.cancel_event),
    path("admin/events/pending/", views.pending_events_admin),
    path("admin/events/upcoming/", views.upcoming_events_admin),
    path("admin/events/past/", views.past_events_admin),
    path("admin/events/cancelled/", views.cancelled_events_admin),
    path('admin/banner/create/', views.create_banner, name="create_banner"),
    
    # New endpoints for refunds and all events
    path('admin/events/all/', views.get_all_events, name="get_all_events"),
    path('admin/pending-refunds/', views.get_pending_refunds, name="get_pending_refunds"),
    path('admin/approve-refund/<int:booking_id>/', views.approve_refund, name="approve_refund"),
    path('admin/reject-refund/<int:booking_id>/', views.reject_refund, name="reject_refund"),
    




   


     
    

]