"""payments/admin.py – Django admin registration for Payment."""

from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display  = [
        "booking_ref", "amount", "payment_method", "payment_status",
        "razorpay_payment_id", "payment_reference", "created_at",
    ]
    list_filter   = ["payment_method", "payment_status"]
    search_fields = [
        "booking__booking_reference",
        "razorpay_order_id", "razorpay_payment_id",
        "payment_reference",
    ]
    date_hierarchy = "created_at"
    readonly_fields = ["razorpay_order_id", "razorpay_payment_id", "razorpay_signature", "created_at", "updated_at"]

    def booking_ref(self, obj):
        return obj.booking.booking_reference
    booking_ref.short_description = "Booking Ref"
