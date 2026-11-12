"""
notifications/models.py
========================
In-app notification model. Notifications are displayed in the mobile app
to inform customers about booking status changes and payment updates.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone


class NotificationType(models.TextChoices):
    BOOKING_SUBMITTED   = "BOOKING_SUBMITTED",   "Booking Request Submitted"
    BOOKING_APPROVED    = "BOOKING_APPROVED",    "Booking Approved"
    BOOKING_REJECTED    = "BOOKING_REJECTED",    "Booking Rejected"
    BOOKING_CONFIRMED   = "BOOKING_CONFIRMED",   "Booking Confirmed"
    BOOKING_CANCELLED   = "BOOKING_CANCELLED",   "Booking Cancelled"
    BOOKING_EXPIRING    = "BOOKING_EXPIRING",    "Booking Expiring Soon"
    PAYMENT_RECEIVED    = "PAYMENT_RECEIVED",    "Payment Received"
    PAYMENT_PENDING     = "PAYMENT_PENDING",     "Payment Due"
    RECEIPT_AVAILABLE   = "RECEIPT_AVAILABLE",   "Receipt Ready to Download"
    GENERAL             = "GENERAL",             "General Notification"


class Notification(models.Model):
    """
    In-app notification delivered to a registered customer.
    Linked optionally to a specific booking for deep-link navigation.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    booking = models.ForeignKey(
        "bookings.Booking",
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name="notifications",
        help_text="Related booking for deep-link navigation in the mobile app.",
    )
    notification_type = models.CharField(
        max_length=30,
        choices=NotificationType.choices,
        default=NotificationType.GENERAL,
        db_index=True,
    )
    title = models.CharField(max_length=150)
    message = models.TextField()
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table    = "notifications_notification"
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_read"]),
        ]

    def __str__(self):
        status = "✓" if self.is_read else "●"
        return f"[{status}] {self.user.mobile_number} – {self.title}"

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=["is_read"])
