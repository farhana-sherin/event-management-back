from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from api.v1.core.views import home


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home, name="home"),
    path("api/v1/customer/", include(("api.v1.customer.urls", "customer"), namespace="customer")),
    path("api/v1/organizer/", include(("api.v1.organizer.urls", "organizer"), namespace="organizer")),
    path("api/v1/payment/", include(("api.v1.payment.urls", "payment"), namespace="payment")),
    path("api/v1/admin/", include(("api.v1.admin.urls", "admin_api"), namespace="admin_api")),
    path("api/v1/core/", include(("api.v1.core.urls", "core"), namespace="core")),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

