"""
Memon Samaj Wadi – Root URL Configuration
All API routes are prefixed with /api/
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django admin (for superuser management)
    path("django-admin/", admin.site.urls),

    # Authentication & User endpoints
    path("api/auth/", include("accounts.urls")),

    # Hall & Availability endpoints
    path("api/hall/", include("bookings.hall_urls")),

    # Booking endpoints
    path("api/bookings/", include("bookings.urls")),

    # Payment endpoints
    path("api/payments/", include("payments.urls")),

    # Receipt & Verification endpoints
    path("api/receipts/", include("receipts.urls")),

    # Notifications endpoints
    path("api/notifications/", include("notifications.urls")),

    # Admin management endpoints
    path("api/admin/", include("bookings.admin_urls")),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
