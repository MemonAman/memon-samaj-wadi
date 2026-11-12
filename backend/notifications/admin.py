"""notifications/admin.py – Django admin registration for Notification."""

from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display  = ["user_mobile", "title", "notification_type", "is_read", "created_at"]
    list_filter   = ["notification_type", "is_read"]
    search_fields = ["user__mobile_number", "user__full_name", "title"]
    date_hierarchy = "created_at"
    readonly_fields = ["created_at"]

    def user_mobile(self, obj):
        return f"{obj.user.full_name} ({obj.user.mobile_number})"
    user_mobile.short_description = "User"
