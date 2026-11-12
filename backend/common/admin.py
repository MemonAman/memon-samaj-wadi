"""common/admin.py – Django admin registration for AuditLog."""

from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display   = ["created_at", "action", "entity_type", "entity_id", "user", "ip_address"]
    list_filter    = ["action", "entity_type"]
    search_fields  = ["entity_id", "user__mobile_number", "description"]
    date_hierarchy = "created_at"
    readonly_fields = [
        "user", "action", "entity_type", "entity_id",
        "description", "ip_address", "changes", "created_at",
    ]

    def has_add_permission(self, request):
        return False   # Audit logs are written by code only

    def has_change_permission(self, request, obj=None):
        return False   # Immutable

    def has_delete_permission(self, request, obj=None):
        return False   # Never deleted

