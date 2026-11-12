"""receipts/admin.py – Django admin registration for Receipt."""

from django.contrib import admin
from .models import Receipt, ReceiptReprint


class ReceiptReprintInline(admin.TabularInline):
    model  = ReceiptReprint
    extra  = 0
    fields = ["reprinted_by", "reason", "reprinted_at"]
    readonly_fields = ["reprinted_at"]


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display   = ["receipt_number", "booking_ref", "issued_at", "issued_by"]
    search_fields  = ["receipt_number", "booking__booking_reference", "qr_verification_code"]
    date_hierarchy = "issued_at"
    readonly_fields = ["qr_verification_code", "created_at"]
    inlines = [ReceiptReprintInline]

    def booking_ref(self, obj):
        return obj.booking.booking_reference
    booking_ref.short_description = "Booking Ref"
