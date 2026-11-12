"""bookings/admin.py – Django admin registration for Hall, Booking, BlockedDate."""

from django.contrib import admin
from django.utils.html import format_html
from .models import Hall, HallImage, BlockedDate, Booking, BookingStatus


class HallImageInline(admin.TabularInline):
    model = HallImage
    extra = 1
    fields = ["image", "caption", "is_primary", "display_order"]


@admin.register(Hall)
class HallAdmin(admin.ModelAdmin):
    list_display  = ["name", "capacity", "booking_price", "advance_amount", "is_active"]
    list_editable = ["is_active"]
    inlines       = [HallImageInline]
    fieldsets = [
        ("Basic Information",   {"fields": ["name", "address", "description", "capacity", "is_active", "samaj_logo"]}),
        ("Pricing",             {"fields": ["booking_price", "advance_amount"]}),
        ("Policy",              {"fields": ["pending_expiry_hours", "payment_rules", "cancellation_rules"]}),
        ("Contact",             {"fields": ["contact_phone", "contact_email"]}),
    ]


@admin.register(BlockedDate)
class BlockedDateAdmin(admin.ModelAdmin):
    list_display  = ["blocked_date", "hall", "reason", "blocked_by", "is_active"]
    list_filter   = ["hall", "is_active"]
    date_hierarchy = "blocked_date"
    search_fields  = ["reason"]


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display   = [
        "booking_reference", "booking_date", "user_name", "function_type",
        "status_badge", "total_amount", "created_at",
    ]
    list_filter    = ["status", "function_type", "hall"]
    search_fields  = ["booking_reference", "user__full_name", "user__mobile_number"]
    date_hierarchy = "booking_date"
    readonly_fields = [
        "booking_reference", "created_at", "updated_at",
        "approved_at", "rejected_at", "cancelled_at",
    ]
    fieldsets = [
        ("Booking",         {"fields": ["booking_reference", "user", "hall", "booking_date", "function_type", "function_description", "customer_address"]}),
        ("Status",          {"fields": ["status", "pending_expires_at"]}),
        ("Financials",      {"fields": ["total_amount", "advance_amount_required"]}),
        ("Admin Decision",  {"fields": ["admin_notes", "rejection_reason", "cancellation_reason"]}),
        ("Approval Audit",  {"fields": ["approved_by", "approved_at", "rejected_by", "rejected_at", "cancelled_by", "cancelled_at"]}),
        ("Timestamps",      {"fields": ["created_at", "updated_at"], "classes": ["collapse"]}),
    ]

    def user_name(self, obj):
        return f"{obj.user.full_name} ({obj.user.mobile_number})"
    user_name.short_description = "Customer"

    def status_badge(self, obj):
        colors = {
            BookingStatus.PENDING:   "#f59e0b",
            BookingStatus.APPROVED:  "#3b82f6",
            BookingStatus.CONFIRMED: "#10b981",
            BookingStatus.REJECTED:  "#ef4444",
            BookingStatus.CANCELLED: "#6b7280",
            BookingStatus.EXPIRED:   "#9ca3af",
        }
        color = colors.get(obj.status, "#6b7280")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:4px;font-size:12px">{}</span>',
            color, obj.get_status_display(),
        )
    status_badge.short_description = "Status"
