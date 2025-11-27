from django.urls import path

from api.v1.customer import views
app_name = 'customer'



urlpatterns = [
    path('login/', views.login,name='login'),
    path('register/',views.register,name='register'),
    path('profile/<int:id>/', views.profile, name='profile'),
    path('profile/update/<int:id>/', views.update_profile, name='update_profile'),
    path("logout/",views.logout,name="logout"),
    path('searchby/category/',views.search_events,name='search'),
    path('events/list/',views.events_list,name="events"),
    path('events/detail/<int:id>/', views.event_detail_customer, name='event_detail'),
    path("booking/detail/<int:booking_id>/", views.booking_detail, name="booking-detail"),

    
    path("booking/cancel/<int:booking_id>/", views.cancel_booking, name="cancel_booking"),
    path("view/all/booking/",views.my_bookings,name="view_booking"),
    path('wishlist/add/<int:id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('wishlist/', views.my_wishlist, name='list_wishlist'),
    path("notification/", views.customer_notifications, name="my_notifications"),
    path("mark-all-read/", views.mark_all_notifications_read, name="mark_all_notifications_read"),
    path("unread-count/", views.unread_notifications_count, name="unread_notifications_count"),
    path("event/explore/categories/", views.explore_categories, name="explore_categories"),
    path("notification/mark-read/<int:id>/", views.mark_notification_read, name="mark_notification_read"),
    path('past-events/',views.past_events, name='customer-past-events'),
    path("tickets/create/", views.create_ticket, name="create_ticket"),
    path("tickets/my/", views.my_tickets, name="my_tickets"),
    path("faqs/", views.list_faqs, name="list_faqs"),
   
    path("banners/", views.banner_list, name="banner-list"),
    path("upcoming/event/", views.upcoming_events, name="upcoming-events"),
    path("featured/event/",views.featured_events,name="featured_events"),
    path("become/organizer/",views.become_organizer,name="become-organizer"),
    path("event/<int:event_id>/rate/", views.rate_event, name="rate_event"),
    path("event/all/ratings/", views.get_all_ratings, name="get_event_ratings"),
    path("recommendations/", views.recommended_events, name="recommended-events"),
    
    









    


]