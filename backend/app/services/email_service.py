"""
Email dispatch service supporting Brevo SMTP and local development modes.
Provides secure, branded HTML/text emails for Email Verification and Password Reset.
"""
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """
    Handles dispatch of authentication-related emails (password reset, email verification).
    Supports Brevo SMTP (and standard SMTP providers) with TLS/STARTTLS.
    In local development without configured SMTP, logs safe development links without exposing secrets.
    """

    @classmethod
    def _is_smtp_configured(cls) -> bool:
        """Checks if all required SMTP credentials and host are present."""
        return bool(
            settings.SMTP_HOST
            and settings.SMTP_USERNAME
            and settings.SMTP_PASSWORD
        )

    @classmethod
    def _send_smtp_message(cls, to_email: str, subject: str, text_body: str, html_body: str) -> bool:
        """
        Connects to the configured SMTP provider (Brevo) and dispatches an email message.
        """
        if not cls._is_smtp_configured():
            if settings.ENVIRONMENT.lower() == "production":
                logger.error("[EmailService] SMTP credentials are not configured in production mode.")
                return False
            logger.info(f"[EmailService DEV] SMTP not configured. Simulated dispatch to '{to_email}' with subject '{subject}'.")
            return True

        # Safeguard: Do not attempt live SMTP network dispatch to RFC-reserved test domains in automated suites
        if to_email.endswith(("@example.test", "@test.local", "@test.invalid")):
            logger.info(f"[EmailService TEST] Simulated dispatch to test recipient '{to_email}'.")
            return True

        from_addr = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>" if settings.SMTP_FROM_NAME else settings.SMTP_FROM_EMAIL

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = from_addr
        msg["To"] = to_email

        msg.attach(MIMEText(text_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        try:
            if settings.SMTP_PORT == 465:
                # Direct SSL
                with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                    server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                    server.send_message(msg)
            else:
                # STARTTLS (Standard Brevo port 587)
                with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                    if settings.SMTP_USE_TLS:
                        server.starttls()
                    server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                    server.send_message(msg)

            logger.info(f"[EmailService] Successfully delivered email '{subject}' to recipient '{to_email}'.")
            return True
        except Exception as exc:
            # Crucial: Log error message without disclosing SMTP_PASSWORD
            logger.error(f"[EmailService] SMTP delivery failure to '{to_email}': {exc.__class__.__name__}: {str(exc)}")
            return False

    # =========================================================================
    # 1. EMAIL VERIFICATION
    # =========================================================================

    @classmethod
    def send_verification_email(cls, to_email: str, verification_token: str, full_name: Optional[str] = None) -> bool:
        """
        Dispatches email address verification link.
        """
        base_url = settings.FRONTEND_BASE_URL.rstrip("/")
        verify_url = f"{base_url}/#/verify-email?token={verification_token}"
        display_name = full_name or "Valued User"
        subject = "Verify your SPECra email"

        text_body = f"""Hello {display_name},

Thank you for registering with SPECra — AI-Powered Product Intelligence for Industrial Commerce.

Please verify your email address by opening the following link in your browser:
{verify_url}

This verification link will expire in {settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES} minutes.

If you did not create a SPECra account, you can safely disregard this email.

Best regards,
The SPECra Team
"""

        html_body = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Verify your SPECra email</title>
</head>
<body style="margin: 0; padding: 0; background-color: #0B0F19; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #E2E8F0;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #0B0F19; padding: 40px 10px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" style="max-width: 580px; background-color: #131B2E; border: 1px solid #1E293B; border-radius: 12px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.5);" cellspacing="0" cellpadding="0">
          
          <!-- Header -->
          <tr>
            <td style="padding: 32px 32px 24px 32px; text-align: left; border-bottom: 1px solid #1E293B; background: linear-gradient(180deg, #182238 0%, #131B2E 100%);">
              <span style="font-size: 24px; font-weight: 800; letter-spacing: -0.5px; color: #38BDF8;">SPEC<span style="color: #6366F1;">ra</span></span>
              <p style="margin: 4px 0 0 0; font-size: 13px; color: #94A3B8; font-weight: 500;">AI-Powered Product Intelligence</p>
            </td>
          </tr>

          <!-- Main Content -->
          <tr>
            <td style="padding: 32px;">
              <h1 style="margin: 0 0 16px 0; font-size: 20px; font-weight: 700; color: #F8FAFC;">Verify your email address</h1>
              <p style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #CBD5E1;">
                Hello <strong>{display_name}</strong>,
              </p>
              <p style="margin: 0 0 24px 0; font-size: 15px; line-height: 1.6; color: #CBD5E1;">
                Thank you for joining SPECra. Please confirm your email address by clicking the button below to activate your account.
              </p>

              <!-- CTA Button -->
              <table role="presentation" cellspacing="0" cellpadding="0" style="margin: 28px 0;">
                <tr>
                  <td align="center" style="border-radius: 8px; background: linear-gradient(135deg, #0EA5E9 0%, #2563EB 100%);">
                    <a href="{verify_url}" target="_blank" style="display: inline-block; padding: 14px 28px; font-size: 15px; font-weight: 600; color: #FFFFFF; text-decoration: none; border-radius: 8px;">
                      Verify Email Address
                    </a>
                  </td>
                </tr>
              </table>

              <p style="margin: 20px 0 8px 0; font-size: 13px; line-height: 1.5; color: #94A3B8;">
                If the button above does not work, copy and paste this link into your browser:
              </p>
              <p style="margin: 0 0 24px 0; font-size: 12px; line-height: 1.4; word-break: break-all; color: #38BDF8;">
                {verify_url}
              </p>

              <div style="border-top: 1px solid #1E293B; padding-top: 16px; margin-top: 24px;">
                <p style="margin: 0; font-size: 13px; line-height: 1.5; color: #64748B;">
                  ⏱️ This link will expire in <strong>{settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES} minutes</strong>.<br>
                  🔒 If you did not create an account with SPECra, please disregard this message.
                </p>
              </div>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding: 20px 32px; background-color: #0F172A; text-align: center; border-top: 1px solid #1E293B;">
              <p style="margin: 0; font-size: 12px; color: #64748B;">
                © 2026 SPECra. Team DEADLOCK — UniHack 2026. All rights reserved.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

        logger.info(f"[EmailService] Verification email prepared for '{to_email}'.")
        return cls._send_smtp_message(to_email, subject, text_body, html_body)

    # =========================================================================
    # 2. PASSWORD RESET
    # =========================================================================

    @classmethod
    def send_password_reset_email(cls, to_email: str, reset_token: str, full_name: Optional[str] = None) -> bool:
        """
        Dispatches password reset link.
        """
        base_url = settings.FRONTEND_BASE_URL.rstrip("/")
        reset_url = f"{base_url}/#/reset-password?token={reset_token}"
        display_name = full_name or "Valued User"
        subject = "Reset your SPECra password"

        text_body = f"""Hello {display_name},

A password reset was requested for your SPECra account.

To choose a new password, open the following link in your browser:
{reset_url}

This password reset link will expire in {settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES} minutes.

If you did not request a password reset, you can safely ignore this email. Your existing password will remain unchanged.

Best regards,
The SPECra Team
"""

        html_body = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Reset your SPECra password</title>
</head>
<body style="margin: 0; padding: 0; background-color: #0B0F19; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #E2E8F0;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #0B0F19; padding: 40px 10px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" style="max-width: 580px; background-color: #131B2E; border: 1px solid #1E293B; border-radius: 12px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.5);" cellspacing="0" cellpadding="0">
          
          <!-- Header -->
          <tr>
            <td style="padding: 32px 32px 24px 32px; text-align: left; border-bottom: 1px solid #1E293B; background: linear-gradient(180deg, #182238 0%, #131B2E 100%);">
              <span style="font-size: 24px; font-weight: 800; letter-spacing: -0.5px; color: #38BDF8;">SPEC<span style="color: #6366F1;">ra</span></span>
              <p style="margin: 4px 0 0 0; font-size: 13px; color: #94A3B8; font-weight: 500;">AI-Powered Product Intelligence</p>
            </td>
          </tr>

          <!-- Main Content -->
          <tr>
            <td style="padding: 32px;">
              <h1 style="margin: 0 0 16px 0; font-size: 20px; font-weight: 700; color: #F8FAFC;">Reset your password</h1>
              <p style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #CBD5E1;">
                Hello <strong>{display_name}</strong>,
              </p>
              <p style="margin: 0 0 24px 0; font-size: 15px; line-height: 1.6; color: #CBD5E1;">
                We received a request to reset the password for your SPECra account. Click the button below to select a new secure password.
              </p>

              <!-- CTA Button -->
              <table role="presentation" cellspacing="0" cellpadding="0" style="margin: 28px 0;">
                <tr>
                  <td align="center" style="border-radius: 8px; background: linear-gradient(135deg, #0EA5E9 0%, #2563EB 100%);">
                    <a href="{reset_url}" target="_blank" style="display: inline-block; padding: 14px 28px; font-size: 15px; font-weight: 600; color: #FFFFFF; text-decoration: none; border-radius: 8px;">
                      Reset Password
                    </a>
                  </td>
                </tr>
              </table>

              <p style="margin: 20px 0 8px 0; font-size: 13px; line-height: 1.5; color: #94A3B8;">
                If the button above does not work, copy and paste this link into your browser:
              </p>
              <p style="margin: 0 0 24px 0; font-size: 12px; line-height: 1.4; word-break: break-all; color: #38BDF8;">
                {reset_url}
              </p>

              <div style="border-top: 1px solid #1E293B; padding-top: 16px; margin-top: 24px;">
                <p style="margin: 0; font-size: 13px; line-height: 1.5; color: #64748B;">
                  ⏱️ This link will expire in <strong>{settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES} minutes</strong>.<br>
                  🔒 If you did not request this password reset, no action is needed. Your password remains unchanged.
                </p>
              </div>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding: 20px 32px; background-color: #0F172A; text-align: center; border-top: 1px solid #1E293B;">
              <p style="margin: 0; font-size: 12px; color: #64748B;">
                © 2026 SPECra. Team DEADLOCK — UniHack 2026. All rights reserved.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

        logger.info(f"[EmailService] Password reset email prepared for '{to_email}'.")
        return cls._send_smtp_message(to_email, subject, text_body, html_body)

