from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse   # ADD THIS


# Default root view
def home(request):
    return JsonResponse({
        "status": "running",
        "message": "Event Management API is live"
    })


urlpatterns = [
    path('', home),  # 👈 DEFAULT ROOT URL

    path('admin/', admin.site.urls),

    path('api/v1/customer/', include("api.v1.customer.urls", namespace='customer')),
    path('api/v1/organizer/', include("api.v1.organizer.urls", namespace='organizer')),
    path('api/v1/payment/', include("api.v1.payment.urls", namespace="payment")),

    # FIX: namespace conflict (admin already used by Django admin)
    path('api/v1/admin/', include("api.v1.admin.urls", namespace="admin_api")),
]


if settings.DEBUG:
    urlpatterns += (
        static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) +
        static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    )
