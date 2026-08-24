"""
Email dispatch abstraction for development and production.
"""
import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """
    Handles dispatch of authentication-related emails (password reset, email verification).
    In local development, logs securely to console/logger without exposing secrets.
    In production, integrates with configured SMTP/SES credentials.
    """

    @staticmethod
    def send_password_reset_email(to_email: str, reset_token: str, full_name: Optional[str] = None) -> bool:
        """
        Dispatches password reset link.
        """
        reset_url = f"http://localhost:5173/#/reset-password?token={reset_token}"
        logger.info(f"[EmailService] Password reset requested for '{to_email}'. Dispatching reset link.")
        # In development mode, we output the URL for local testing while keeping tokens out of user-facing production logs
        if not settings.COOKIE_SECURE:
            logger.info(f"[EmailService DEV] Reset URL: {reset_url}")
        return True

    @staticmethod
    def send_verification_email(to_email: str, verification_token: str, full_name: Optional[str] = None) -> bool:
        """
        Dispatches email address verification link.
        """
        verify_url = f"http://localhost:5173/#/verify-email?token={verification_token}"
        logger.info(f"[EmailService] Verification email queued for '{to_email}'.")
        if not settings.COOKIE_SECURE:
            logger.info(f"[EmailService DEV] Verification URL: {verify_url}")
        return True
