"""
accounts/models.py
Custom User model for Memon Samaj Wadi.
Uses mobile_number as the primary authentication identifier (no username/password).
"""

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone


class UserRole(models.TextChoices):
    CUSTOMER = "CUSTOMER", "Customer"
    ADMIN = "ADMIN", "Admin"


class UserManager(BaseUserManager):
    """Custom manager that uses mobile_number instead of username."""

    def create_user(self, mobile_number, full_name, **extra_fields):
        if not mobile_number:
            raise ValueError("Mobile number is required.")
        if not full_name:
            raise ValueError("Full name is required.")

        extra_fields.setdefault("role", UserRole.CUSTOMER)
        extra_fields.setdefault("is_active", True)

        user = self.model(
            mobile_number=mobile_number,
            full_name=full_name,
            **extra_fields,
        )
        # OTP-based auth — no password stored for customers
        user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_admin_user(self, mobile_number, full_name, password, **extra_fields):
        """Create an admin user with a password (for dashboard login)."""
        extra_fields.setdefault("role", UserRole.ADMIN)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_active", True)

        user = self.model(
            mobile_number=mobile_number,
            full_name=full_name,
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, mobile_number, full_name, password, **extra_fields):
        """Create a Django superuser (for manage.py createsuperuser)."""
        extra_fields.setdefault("role", UserRole.ADMIN)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        return self.create_admin_user(mobile_number, full_name, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model.

    Customers authenticate via OTP (no password).
    Admins authenticate via mobile_number + password.
    """

    mobile_number = models.CharField(
        max_length=15,
        unique=True,
        db_index=True,
        help_text="Mobile number including country code, e.g. +919876543210",
    )
    full_name = models.CharField(max_length=150)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    role = models.CharField(
        max_length=10,
        choices=UserRole.choices,
        default=UserRole.CUSTOMER,
        db_index=True,
    )

    # Django auth required fields
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    # Use mobile_number as the unique identifier
    USERNAME_FIELD = "mobile_number"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        db_table = "accounts_user"
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.full_name} ({self.mobile_number})"

    @property
    def is_admin(self):
        return self.role == UserRole.ADMIN

    @property
    def is_customer(self):
        return self.role == UserRole.CUSTOMER


class OTPVerification(models.Model):
    """
    Stores OTP codes for mobile verification.
    One active record per mobile number.
    """

    mobile_number = models.CharField(max_length=15, db_index=True)
    otp_code = models.CharField(max_length=6)
    purpose = models.CharField(
        max_length=20,
        choices=[
            ("REGISTER", "Registration"),
            ("LOGIN", "Login"),
        ],
        default="LOGIN",
    )
    attempts = models.PositiveSmallIntegerField(default=0)
    is_verified = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "accounts_otp_verification"
        verbose_name = "OTP Verification"
        verbose_name_plural = "OTP Verifications"
        ordering = ["-created_at"]

    def __str__(self):
        return f"OTP for {self.mobile_number} (expires {self.expires_at})"

    def is_expired(self):
        return timezone.now() > self.expires_at

    def is_valid(self):
        return not self.is_verified and not self.is_expired()
