from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Log PQC status once at startup
if not settings.USE_REAL_PQC:
    logger.warning("USE_REAL_PQC=false — do NOT claim PQC to any customer")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Security headers
        response.headers["Strict-Transport-Security"] = \
            "max-age=31536000; includeSubDomains; preload"
        response.headers["Content-Security-Policy"] = \
            "default-src 'self'; script-src 'self'; object-src 'none'"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = \
            "camera=(), microphone=(), geolocation=()"
        response.headers["X-PQC-Status"] = "enabled" if settings.USE_REAL_PQC else "disabled"

        return response


def get_security_headers():
    """Return security headers dict"""
    return {
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
        "Content-Security-Policy": "default-src 'self'; script-src 'self'; object-src 'none'",
        "X-Frame-Options": "DENY",
        "X-Content-Type-Options": "nosniff",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
        "X-PQC-Status": "enabled" if settings.USE_REAL_PQC else "disabled"
    }
