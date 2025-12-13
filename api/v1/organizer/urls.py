from django.urls import path

from api.v1.organizer import views
app_name = 'organizer'


urlpatterns = [
    path("register/",views.register_organizer,name="register"),
    path("event/list/",views. my_events,name="event"),
    path('events/detail/<int:id>/', views.event_detail_organizer, name='event_detail'),
    path("event/create/",views.create_event,name="createEvent"),
    path("event/update/<int:id>/",views.update_event,name="updateEvent"),
    path("event/delete/<int:id>/",views.delete_event,name="deleteeEvent"),
    path("tickets/update/<int:id>/", views.update_ticket_status, name="update_ticket_status"),
    path("faqs/create/", views.create_faq, name="create_faq"),
    path("faqs/update/<int:id>/", views.update_faq, name="update_faq"),
    path("faqs/delete/<int:id>/", views.delete_faq, name="delete_faq"),
    path("organizer/payment/",views.organizer_payments,name="organzier-payments"),
    path("cancelled/bookings/",views.cancelled_bookings,name="cancelled-booking"),
    path("dashboard/",views.organizer_dashboard,name="dashboard"),
    path("booking/detail/<int:booking_id>/",views.booking_detail,name="event-booking"),
    path("event/booking/all/",views.organizer_all_bookings,name="event-booking"),
    path("event/category/",views.event_categories,name="event-category"),
    path("organizer/analytics/",views.organizer_analytics,name="organizer-analytics"),
    path("events/pending/", views.pending_events),
    path("events/upcoming/", views.upcoming_events),
    path("events/past/", views.past_events),
    path("events/cancelled/", views.cancelled_events),
    
    path("revenue/by/peroid/", views.revenue_by_period,name="revenue-by-period"),
    path("revenue/by/category/", views.revenue_by_category,name="revenue-by-category"),
    path("revenue/sold/", views.tickets_sold_trends,name="revenue-sold"),
    path("notifications/", views.organizer_notifications,name="organizer-notification"),
    path("event/ratings/", views.organizer_event_ratings, name="organizer_event_ratings"),

    path("profile/", views.organizer_profile, name="organizer_profile"),
    path("profile/update/", views.update_organizer_profile, name="update_organizer_profile"),
    path("logout/",views.logout,name="logout"),

    
]