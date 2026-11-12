"""
bookings/models.py
==================
Hall, HallImage, BlockedDate, and Booking models for Memon Samaj Wadi.

Key design decisions:
- Booking uses a PostgreSQL partial UniqueConstraint to guarantee only ONE
  active reservation (PENDING | APPROVED | CONFIRMED) per hall per date.
- Atomic transactions + select_for_update() in business logic prevent race
  conditions when two users request the same date simultaneously.
- Financial amounts (total, advance) are snapshotted at booking time so
  future hall price changes do not affect existing bookings.
"""

from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone


# ─── Choices ─────────────────────────────────────────────────────────────────

class FunctionType(models.TextChoices):
    MARRIAGE           = "MARRIAGE",          "Marriage"
    WEDDING_RECEPTION  = "WEDDING_RECEPTION",  "Wedding Reception"
    ENGAGEMENT         = "ENGAGEMENT",         "Engagement"
    FAMILY_FUNCTION    = "FAMILY_FUNCTION",    "Family Function"
    OTHER              = "OTHER",              "Other"


class BookingStatus(models.TextChoices):
    PENDING    = "PENDING",    "Pending Approval"
    APPROVED   = "APPROVED",   "Approved – Awaiting Payment"
    CONFIRMED  = "CONFIRMED",  "Confirmed"
    REJECTED   = "REJECTED",   "Rejected by Admin"
    CANCELLED  = "CANCELLED",  "Cancelled"
    EXPIRED    = "EXPIRED",    "Pending Request Expired"


# Statuses that hold a calendar date (prevent other bookings on same date)
ACTIVE_STATUSES = [
    BookingStatus.PENDING,
    BookingStatus.APPROVED,
    BookingStatus.CONFIRMED,
]

# Statuses that release a calendar date back to available
INACTIVE_STATUSES = [
    BookingStatus.REJECTED,
    BookingStatus.CANCELLED,
    BookingStatus.EXPIRED,
]


# ─── Hall ─────────────────────────────────────────────────────────────────────

class Hall(models.Model):
    """
    Community hall (Samaj Wadi).
    Structured for one hall in v1 but ready for multi-hall expansion.
    All configurable fields are managed through the admin dashboard Settings page.
    """

    name = models.CharField(
        max_length=150,
        default="[HALL NAME – configure in admin settings]",
    )
    address = models.TextField(
        default="[HALL ADDRESS – configure in admin settings]",
    )
    description = models.TextField(
        blank=True,
        default="",
        help_text="Description displayed to customers in the mobile app.",
    )
    capacity = models.PositiveIntegerField(
        default=500,
        help_text="Maximum guest capacity.",
    )

    # Pricing (admin-configurable)
    booking_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Full 24-hour booking charge in INR.",
    )
    advance_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Advance deposit required after admin approval.",
    )

    # Policy (admin-configurable)
    pending_expiry_hours = models.PositiveIntegerField(
        default=24,
        help_text="Hours before an un-actioned pending booking expires.",
    )
    payment_rules = models.TextField(
        blank=True,
        default="",
        help_text="Payment terms displayed to customers.",
    )
    cancellation_rules = models.TextField(
        blank=True,
        default="",
        help_text="Cancellation and refund policy.",
    )

    # Contact & Branding
    contact_phone = models.CharField(max_length=20, blank=True, default="")
    contact_email = models.EmailField(blank=True, null=True)
    samaj_logo = models.ImageField(
        upload_to="hall/logos/",
        blank=True,
        null=True,
        help_text="Logo used in PDF Pavti and app branding.",
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table    = "bookings_hall"
        verbose_name = "Hall"
        verbose_name_plural = "Halls"

    def __str__(self):
        return f"{self.name} (capacity: {self.capacity})"


class HallImage(models.Model):
    """Gallery images shown in the customer mobile app."""

    hall = models.ForeignKey(
        Hall,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.ImageField(upload_to="hall/gallery/")
    caption = models.CharField(max_length=150, blank=True)
    is_primary = models.BooleanField(
        default=False,
        help_text="Shown as the main hall photo on the home screen.",
    )
    display_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table    = "bookings_hall_image"
        verbose_name = "Hall Image"
        verbose_name_plural = "Hall Images"
        ordering = ["display_order", "-is_primary"]

    def __str__(self):
        return f"{self.hall.name} – image {self.pk} ({self.caption or 'no caption'})"


# ─── BlockedDate ──────────────────────────────────────────────────────────────

class BlockedDate(models.Model):
    """
    Dates manually blocked by the Samaj Administrator.
    Blocked dates cannot be reserved by any customer.
    Soft-delete via is_active=False instead of hard delete to preserve audit history.
    """

    hall = models.ForeignKey(
        Hall,
        on_delete=models.CASCADE,
        related_name="blocked_dates",
    )
    blocked_date = models.DateField(db_index=True)
    reason = models.CharField(
        max_length=255,
        help_text='E.g. "Annual Maintenance", "Samaj AGM 2026"',
    )
    blocked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="blocked_dates_created",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Set False to unblock without deleting the record.",
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table    = "bookings_blocked_date"
        verbose_name = "Blocked Date"
        verbose_name_plural = "Blocked Dates"
        ordering = ["-blocked_date"]
        constraints = [
            models.UniqueConstraint(
                fields=["hall", "blocked_date"],
                condition=models.Q(is_active=True),
                name="unique_active_blocked_date_per_hall",
            )
        ]

    def __str__(self):
        return f"{self.blocked_date} – {self.hall.name} [{self.reason}]"


# ─── Booking ──────────────────────────────────────────────────────────────────

class Booking(models.Model):
    """
    Primary 24-hour hall reservation.

    CRITICAL CONSTRAINT:
        unique_active_hall_booking_date – PostgreSQL partial unique index that
        ensures only ONE active booking (PENDING | APPROVED | CONFIRMED) can
        ever exist per hall per date. This is the last line of defence against
        double-bookings. Combined with select_for_update() in the booking
        creation view for full concurrency safety.

    Reference format: MSW-YYYY-NNNN  (e.g. MSW-2026-0001)
    """

    booking_reference = models.CharField(
        max_length=30,
        unique=True,
        db_index=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="bookings",
    )
    hall = models.ForeignKey(
        Hall,
        on_delete=models.PROTECT,
        related_name="bookings",
    )
    booking_date = models.DateField(db_index=True)

    function_type = models.CharField(
        max_length=30,
        choices=FunctionType.choices,
        default=FunctionType.MARRIAGE,
    )
    function_description = models.TextField(blank=True)
    customer_address = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=BookingStatus.choices,
        default=BookingStatus.PENDING,
        db_index=True,
    )

    # Financial snapshots at booking creation time (not affected by later hall price changes)
    total_amount = models.DecimalField(
        max_digits=10, decimal_places=2,
        help_text="Snapshot of hall booking_price at time of booking.",
    )
    advance_amount_required = models.DecimalField(
        max_digits=10, decimal_places=2,
        help_text="Snapshot of hall advance_amount at time of booking.",
    )

    # Admin decision fields
    admin_notes        = models.TextField(blank=True)
    rejection_reason   = models.TextField(blank=True)
    cancellation_reason = models.TextField(blank=True)

    # Approval audit
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="approved_bookings",
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    # Rejection audit
    rejected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="rejected_bookings",
    )
    rejected_at = models.DateTimeField(null=True, blank=True)

    # Cancellation audit
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="cancelled_bookings",
    )
    cancelled_at = models.DateTimeField(null=True, blank=True)

    # Auto-expiry: pending bookings expire after hall.pending_expiry_hours
    pending_expires_at = models.DateTimeField(
        null=True, blank=True, db_index=True,
        help_text="Deadline after which this pending booking auto-expires.",
    )

    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table    = "bookings_booking"
        verbose_name = "Booking"
        verbose_name_plural = "Bookings"
        ordering = ["-booking_date", "-created_at"]
        indexes = [
            models.Index(fields=["status", "booking_date"]),
            models.Index(fields=["user", "status"]),
            models.Index(fields=["pending_expires_at"]),
        ]
        constraints = [
            # THE most important constraint in this entire project.
            # Prevents any two active reservations on the same hall+date.
            models.UniqueConstraint(
                fields=["hall", "booking_date"],
                condition=models.Q(status__in=ACTIVE_STATUSES),
                name="unique_active_hall_booking_date",
            )
        ]

    def __str__(self):
        return (
            f"{self.booking_reference} | {self.booking_date} | "
            f"{self.user.full_name} | {self.get_status_display()}"
        )

    # ── Computed properties ──────────────────────────────────────────────────

    @property
    def is_active_reservation(self) -> bool:
        """True if this booking currently holds the calendar date."""
        return self.status in ACTIVE_STATUSES

    @property
    def is_pending_expired(self) -> bool:
        """True if a PENDING booking has crossed its expiry deadline."""
        return (
            self.status == BookingStatus.PENDING
            and self.pending_expires_at is not None
            and timezone.now() > self.pending_expires_at
        )

    @property
    def amount_paid(self) -> Decimal:
        """Sum of all PAID payment records for this booking."""
        from payments.models import PaymentStatus
        result = self.payments.filter(
            payment_status=PaymentStatus.SUCCESS
        ).aggregate(total=models.Sum("amount"))
        return result["total"] or Decimal("0.00")

    @property
    def balance_amount(self) -> Decimal:
        """Remaining unpaid amount."""
        return max(Decimal("0.00"), self.total_amount - self.amount_paid)

    @property
    def is_advance_satisfied(self) -> bool:
        """True when at least the required advance has been paid."""
        return self.amount_paid >= self.advance_amount_required

    @property
    def is_fully_paid(self) -> bool:
        """True when the full booking amount has been cleared."""
        return self.amount_paid >= self.total_amount
