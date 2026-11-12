"""
receipts/models.py
==================
Official digital booking receipt (Pavti) generated as a PDF by ReportLab.

Each confirmed booking gets one Receipt.
Reprint history is tracked via the ReceiptReprint model.
QR verification code links to a public endpoint that shows minimal safe info.
"""

import uuid
from django.db import models
from django.utils import timezone


class Receipt(models.Model):
    """
    Official Pavti record. PDF is generated automatically when a booking
    meets its confirmation conditions (admin-approved + payment policy met).

    receipt_number format: RCP-YYYY-NNNNNN  e.g. RCP-2026-000001
    qr_verification_code: UUID4 used as the QR payload – links to
        GET /api/receipts/verify/<code>/  (public, limited info only)
    """

    booking = models.OneToOneField(
        "bookings.Booking",
        on_delete=models.PROTECT,
        related_name="receipt",
    )
    receipt_number = models.CharField(
        max_length=30,
        unique=True,
        db_index=True,
    )
    qr_verification_code = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        db_index=True,
        editable=False,
        help_text="UUID embedded in QR code for public verification.",
    )
    pdf_file = models.FileField(
        upload_to="receipts/pdfs/",
        blank=True,
        null=True,
        help_text="Generated PDF Pavti stored in configured storage backend.",
    )
    issued_at = models.DateTimeField(
        default=timezone.now,
        help_text="Timestamp shown on the official receipt.",
    )
    issued_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="receipts_issued",
        help_text="Admin who triggered Pavti generation (null = auto-generated).",
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table    = "receipts_receipt"
        verbose_name = "Receipt (Pavti)"
        verbose_name_plural = "Receipts (Pavti)"
        ordering = ["-issued_at"]

    def __str__(self):
        return (
            f"{self.receipt_number} | "
            f"Booking: {self.booking.booking_reference} | "
            f"{self.issued_at.strftime('%d %b %Y')}"
        )


class ReceiptReprint(models.Model):
    """
    Tracks every time a receipt is reprinted or regenerated.
    Preserves the complete audit trail for compliance purposes.
    """

    receipt = models.ForeignKey(
        Receipt,
        on_delete=models.CASCADE,
        related_name="reprints",
    )
    reprinted_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="reprints_performed",
    )
    reason = models.CharField(
        max_length=255,
        blank=True,
        help_text='E.g. "Customer copy lost", "Correction of typo"',
    )
    reprinted_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table    = "receipts_reprint"
        verbose_name = "Receipt Reprint"
        verbose_name_plural = "Receipt Reprints"
        ordering = ["-reprinted_at"]

    def __str__(self):
        return (
            f"Reprint of {self.receipt.receipt_number} "
            f"at {self.reprinted_at.strftime('%d %b %Y %H:%M')}"
        )
