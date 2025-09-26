from django.urls import path

from api.v1.admin import views
app_name = 'admin'



urlpatterns = [

    path('admin/dashboard-summary/', views.admin_dashboard_summary,name='admin_dashboard_summary'),
    path('users/', views.user_list, name='user-list'),          # GET all users
    path('users/<int:pk>/', views.user_delete, name='user-delete'), # DELETE
    path('users/<int:pk>/edit/', views.user_update, name='user-update'),
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
    path("events/<int:pk>/approve/", views.approve_event),
    path("events/<int:pk>/deactivate/", views.deactivate_event),
    path("events/<int:pk>/cancel/", views.cancel_event),
    path("events/pending/", views.pending_events_admin),
    path("events/upcoming/", views.upcoming_events_admin),
    path("events/past/", views.past_events_admin),
    path("events/cancelled/", views.cancelled_events_admin),
    path('admin/banner/create/', views.create_banner, name="create_banner"),
    




   


     
    

]