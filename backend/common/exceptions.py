"""
common/exceptions.py
Custom exception handler for DRF.
Returns consistent JSON error responses across all API endpoints.
"""

import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger("memon_samaj")


def custom_exception_handler(exc, context):
    """
    Custom exception handler that wraps DRF default responses in a
    consistent format:
        {
            "success": false,
            "error": {
                "code": "ERROR_CODE",
                "message": "Human-readable message",
                "details": { ... }   # optional field-level errors
            }
        }
    """
    # Let DRF handle the exception first
    response = exception_handler(exc, context)

    if response is not None:
        error_data = {
            "success": False,
            "error": {
                "code": _get_error_code(response.status_code),
                "message": _get_error_message(response.data),
                "details": response.data if isinstance(response.data, dict) else {},
            },
        }
        response.data = error_data
        logger.warning(
            "API error %s in %s.%s: %s",
            response.status_code,
            context["view"].__class__.__name__,
            getattr(context.get("request"), "method", "UNKNOWN"),
            exc,
        )

    return response


def _get_error_code(status_code: int) -> str:
    codes = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        422: "UNPROCESSABLE_ENTITY",
        429: "RATE_LIMIT_EXCEEDED",
        500: "INTERNAL_SERVER_ERROR",
    }
    return codes.get(status_code, "ERROR")


def _get_error_message(data) -> str:
    if isinstance(data, str):
        return data
    if isinstance(data, list) and data:
        return str(data[0])
    if isinstance(data, dict):
        # Try common message keys
        for key in ("detail", "message", "non_field_errors"):
            if key in data:
                val = data[key]
                if isinstance(val, list):
                    return str(val[0])
                return str(val)
        # Return first field error
        for key, val in data.items():
            if isinstance(val, list):
                return f"{key}: {val[0]}"
            return f"{key}: {val}"
    return "An unexpected error occurred."

