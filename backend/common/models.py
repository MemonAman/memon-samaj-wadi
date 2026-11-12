"""
common/models.py
=================
AuditLog: immutable record of all critical admin, financial and booking changes.
record_audit(): convenience helper called throughout the codebase.
"""

import logging
from django.db import models
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger("memon_samaj")


class AuditAction(models.TextChoices):
    # Booking lifecycle
    BOOKING_CREATED   = "BOOKING_CREATED",   "Booking Request Created"
    BOOKING_APPROVED  = "BOOKING_APPROVED",  "Booking Approved by Admin"
    BOOKING_REJECTED  = "BOOKING_REJECTED",  "Booking Rejected by Admin"
    BOOKING_CANCELLED = "BOOKING_CANCELLED", "Booking Cancelled"
    BOOKING_EXPIRED   = "BOOKING_EXPIRED",   "Booking Request Expired"
    BOOKING_CONFIRMED = "BOOKING_CONFIRMED", "Booking Confirmed"
    # Payments
    PAYMENT_INITIATED        = "PAYMENT_INITIATED",        "Payment Initiated (Razorpay)"
    PAYMENT_SUCCESS          = "PAYMENT_SUCCESS",          "Online Payment Verified"
    PAYMENT_FAILED           = "PAYMENT_FAILED",           "Online Payment Failed"
    OFFLINE_PAYMENT_RECORDED = "OFFLINE_PAYMENT_RECORDED", "Offline Cash Payment Recorded"
    # Calendar & Hall
    DATE_BLOCKED          = "DATE_BLOCKED",          "Date Manually Blocked by Admin"
    DATE_UNBLOCKED        = "DATE_UNBLOCKED",        "Date Unblocked by Admin"
    HALL_SETTINGS_UPDATED = "HALL_SETTINGS_UPDATED", "Hall Settings Updated"
    # Receipts
    RECEIPT_GENERATED = "RECEIPT_GENERATED", "Receipt Generated"
    RECEIPT_REPRINTED = "RECEIPT_REPRINTED", "Receipt Reprinted"
    # Security & Admin
    ADMIN_LOGIN          = "ADMIN_LOGIN",          "Admin Logged In"
    USER_ACCESS_CHANGED  = "USER_ACCESS_CHANGED",  "User Access Modified"


class AuditLog(models.Model):
    """
    Immutable audit entry. Never edited or deleted after creation.
    Admin panel enforces no add/change/delete permissions.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="audit_logs",
        help_text="Actor who performed the action (null = automated system action).",
    )
    action = models.CharField(max_length=60, choices=AuditAction.choices, db_index=True)
    entity_type = models.CharField(
        max_length=50, db_index=True,
        help_text="Model name e.g. Booking, Payment, Hall, Receipt",
    )
    entity_id = models.CharField(
        max_length=100, db_index=True,
        help_text="PK or reference of the affected entity.",
    )
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    changes = models.JSONField(
        null=True, blank=True,
        help_text="JSON snapshot of before/after values.",
    )
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table    = "common_audit_log"
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["entity_type", "entity_id"]),
            models.Index(fields=["action", "created_at"]),
        ]

    def __str__(self):
        actor = self.user.mobile_number if self.user else "System"
        ts = self.created_at.strftime("%Y-%m-%d %H:%M")
        return f"[{ts}] {self.action} on {self.entity_type}#{self.entity_id} by {actor}"


def record_audit(
    action: str,
    entity_type: str,
    entity_id,
    description: str,
    user=None,
    ip_address: str | None = None,
    changes: dict | None = None,
) -> "AuditLog | None":
    """
    Safe helper to write an audit entry.
    Failure is logged but never raises — audit must never crash a business tx.
    """
    try:
        return AuditLog.objects.create(
            user=user,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id),
            description=description,
            ip_address=ip_address,
            changes=changes,
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("AuditLog write failed: %s", exc)
        return None

