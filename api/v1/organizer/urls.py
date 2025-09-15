from django.urls import path

from api.v1.organizer import views
app_name = 'organizer'


urlpatterns = [
    path("register/",views.register_organizer,name="register"),
    path("event/list/",views. my_events,name="event"),
    path('events/detail/<int:id>/', views.event_detail_organizer, name='event_detail'),
    path("event/create",views.create_event,name="createEvent"),
    path("event/update/<int:id>/",views.update_event,name="updateEvent"),
    path("event/delete/<int:id>/",views.delete_event,name="deleteeEvent"),
    path("tickets/update/<int:id>/", views.update_ticket_status, name="update_ticket_status"),
    path("faqs/create/", views.create_faq, name="create_faq"),
    path("faqs/update/<int:id>/", views.update_faq, name="update_faq"),
    path("faqs/delete/<int:id>/", views.delete_faq, name="delete_faq"),
    path("logout/",views.logout,name="logout"),
    
]