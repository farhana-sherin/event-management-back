from django.urls import path

from api.v1.payment import views
app_name = 'payment'



urlpatterns = [
    path("payment/create/<int:id>/",views.create_payment,name="payment"),
    path("payment/confirmed/<int:id>/",views.confirm_payment,name="payment_confirmed"),
]