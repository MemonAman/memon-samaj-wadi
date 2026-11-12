"""
payments/models.py
==================
Payment model supporting both online (Razorpay) and offline (cash) payments.
Multiple payment records per booking allow partial / instalment payments.

IMPORTANT SECURITY NOTE:
    Online payments are NEVER marked successful based on frontend reports.
    Backend verifies Razorpay signature before marking PaymentStatus.SUCCESS.
"""

from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone


class PaymentMethod(models.TextChoices):
    ONLINE  = "ONLINE",  "Online (Razorpay)"
    OFFLINE = "OFFLINE", "Offline (Cash at Office)"


class PaymentStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    SUCCESS = "SUCCESS", "Successful"
    FAILED  = "FAILED",  "Failed"
    REFUNDED = "REFUNDED", "Refunded"


class Payment(models.Model):
    """
    One payment transaction for a booking.
    A single booking can have multiple Payment records (partial payments).

    For ONLINE payments:
        - razorpay_order_id  : created by backend via Razorpay API
        - razorpay_payment_id: returned by Razorpay checkout
        - razorpay_signature : HMAC-SHA256 verified exclusively on the backend

    For OFFLINE payments:
        - received_by: admin who accepted the cash
        - payment_reference: receipt slip / voucher number
    """

    booking = models.ForeignKey(
        "bookings.Booking",
        on_delete=models.PROTECT,
        related_name="payments",
    )
    payment_method = models.CharField(
        max_length=10,
        choices=PaymentMethod.choices,
    )
    payment_status = models.CharField(
        max_length=10,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        db_index=True,
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Amount paid in this transaction (INR).",
    )

    # ── Online (Razorpay) fields ──────────────────────────────────────────────
    razorpay_order_id = models.CharField(
        max_length=100, blank=True,
        help_text="Razorpay Order ID created by backend (order_XXXXXXXX).",
    )
    razorpay_payment_id = models.CharField(
        max_length=100, blank=True,
        help_text="Razorpay Payment ID from checkout (pay_XXXXXXXX).",
    )
    razorpay_signature = models.CharField(
        max_length=255, blank=True,
        help_text="HMAC-SHA256 signature verified by backend only.",
    )

    # ── Offline (cash) fields ─────────────────────────────────────────────────
    payment_reference = models.CharField(
        max_length=100, blank=True,
        help_text="Cash receipt / voucher number for offline payments.",
    )
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="cash_payments_received",
        help_text="Admin who physically received the cash.",
    )
    payment_date = models.DateField(
        null=True, blank=True,
        help_text="Date cash was received at the Samaj office.",
    )
    notes = models.TextField(
        blank=True,
        help_text="Any additional notes (e.g. cheque number, partial reason).",
    )

    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table    = "payments_payment"
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["booking", "payment_status"]),
            models.Index(fields=["payment_method", "created_at"]),
        ]

    def __str__(self):
        return (
            f"₹{self.amount} | {self.get_payment_method_display()} | "
            f"{self.get_payment_status_display()} | "
            f"Booking: {self.booking.booking_reference}"
        )
