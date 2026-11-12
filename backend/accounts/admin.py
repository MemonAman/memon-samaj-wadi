"""accounts/admin.py – Django admin registration for User and OTPVerification."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, OTPVerification


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display   = ["mobile_number", "full_name", "role", "is_active", "created_at"]
    list_filter    = ["role", "is_active"]
    search_fields  = ["mobile_number", "full_name", "email"]
    ordering       = ["-created_at"]
    readonly_fields = ["created_at", "updated_at", "last_login"]

    fieldsets = [
        ("Account",       {"fields": ["mobile_number", "full_name", "email", "address"]}),
        ("Role & Access", {"fields": ["role", "is_active", "is_staff", "is_superuser"]}),
        ("Password",      {"fields": ["password"]}),
        ("Timestamps",    {"fields": ["last_login", "created_at", "updated_at"], "classes": ["collapse"]}),
    ]
    add_fieldsets = [
        (None, {
            "classes": ["wide"],
            "fields":  ["mobile_number", "full_name", "role", "password1", "password2"],
        }),
    ]

    # Required by BaseUserAdmin
    filter_horizontal = ()
    list_display_links = ["mobile_number"]


@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    list_display  = ["mobile_number", "purpose", "is_verified", "attempts", "expires_at", "created_at"]
    list_filter   = ["purpose", "is_verified"]
    search_fields = ["mobile_number"]
    readonly_fields = ["otp_code", "created_at"]
