from django.urls import path

from api.v1.payment import views
app_name = 'payment'



urlpatterns = [
   path("bookings/create/", views.create_booking, name="create-booking"),
    path("payments/create-checkout-session/<int:booking_id>/", views.create_checkout_session, name="create-checkout-session"),
    path("payments/webhook/", views.stripe_webhook, name="stripe-webhook"),
    path("increment/<int:event_id>/",views.increment_ticket,name="increment"),
    path("decrement/<int:event_id>/",views.decrement_ticket,name="decrement"),

]