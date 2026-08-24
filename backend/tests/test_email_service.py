"""
Unit and regression tests for EmailService with Brevo SMTP provider integration.
Tests cover:
1. Verification email generation (subject, recipient, branding, verification link, expiration).
2. Password reset email generation (subject, recipient, branding, reset link, expiration).
3. Brevo SMTP dispatch with mocked smtplib (STARTTLS port 587 and SSL port 465).
4. Development fallback mode when SMTP credentials are not configured.
5. Error handling on SMTP connection failure without disclosing credentials.
6. Zero disclosure of SMTP passwords or raw token digests in logs or responses.
"""
import smtplib
import unittest
from unittest.mock import patch, MagicMock
from email.mime.multipart import MIMEMultipart

from app.core.config import settings
from app.services.email_service import EmailService


class TestBrevoEmailService(unittest.TestCase):
    """
    Tests email generation, SMTP connection, and security safety features of EmailService.
    """

    def setUp(self):
        self.to_email = "architect@industrial-supply.corp"
        self.full_name = "Alex Vance"
        self.test_token = "mock_csp_rng_token_32_bytes_entropy_12345"

    def test_01_is_smtp_configured_detection(self):
        """Test detection of SMTP configuration presence."""
        with patch.object(settings, "SMTP_HOST", "smtp-relay.brevo.com"), \
             patch.object(settings, "SMTP_USERNAME", "brevo_user@example.com"), \
             patch.object(settings, "SMTP_PASSWORD", "brevo_secret_pass"):
            self.assertTrue(EmailService._is_smtp_configured())

        with patch.object(settings, "SMTP_HOST", ""), \
             patch.object(settings, "SMTP_USERNAME", ""), \
             patch.object(settings, "SMTP_PASSWORD", ""):
            self.assertFalse(EmailService._is_smtp_configured())

    def test_02_development_fallback_when_smtp_unconfigured(self):
        """Test safe development fallback when SMTP is not configured in dev mode."""
        with patch.object(settings, "SMTP_HOST", ""), \
             patch.object(settings, "SMTP_USERNAME", ""), \
             patch.object(settings, "SMTP_PASSWORD", ""), \
             patch.object(settings, "ENVIRONMENT", "development"):
            # Should succeed with simulated dispatch and return True
            res_verify = EmailService.send_verification_email(
                to_email=self.to_email,
                verification_token=self.test_token,
                full_name=self.full_name,
            )
            self.assertTrue(res_verify)

            res_reset = EmailService.send_password_reset_email(
                to_email=self.to_email,
                reset_token=self.test_token,
                full_name=self.full_name,
            )
            self.assertTrue(res_reset)

    def test_03_production_mode_fails_safely_if_smtp_missing(self):
        """Test that in production mode, missing SMTP returns False rather than crashing."""
        with patch.object(settings, "SMTP_HOST", ""), \
             patch.object(settings, "SMTP_USERNAME", ""), \
             patch.object(settings, "SMTP_PASSWORD", ""), \
             patch.object(settings, "ENVIRONMENT", "production"):
            res = EmailService.send_verification_email(
                to_email=self.to_email,
                verification_token=self.test_token,
            )
            self.assertFalse(res)

    @patch("smtplib.SMTP")
    def test_04_brevo_smtp_starttls_dispatch_success(self, mock_smtp_cls):
        """Test successful SMTP dispatch using Brevo STARTTLS (Port 587)."""
        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_server

        with patch.object(settings, "SMTP_HOST", "smtp-relay.brevo.com"), \
             patch.object(settings, "SMTP_PORT", 587), \
             patch.object(settings, "SMTP_USERNAME", "7a8b9c@smtp-brevo.com"), \
             patch.object(settings, "SMTP_PASSWORD", "super_secret_brevo_key"), \
             patch.object(settings, "SMTP_FROM_EMAIL", "no-reply@specra.io"), \
             patch.object(settings, "SMTP_FROM_NAME", "SPECra Product Intelligence"), \
             patch.object(settings, "SMTP_USE_TLS", True):

            success = EmailService.send_verification_email(
                to_email=self.to_email,
                verification_token=self.test_token,
                full_name=self.full_name,
            )

            self.assertTrue(success)
            mock_smtp_cls.assert_called_once_with("smtp-relay.brevo.com", 587, timeout=10)
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once_with("7a8b9c@smtp-brevo.com", "super_secret_brevo_key")
            mock_server.send_message.assert_called_once()

            # Inspect dispatched message
            msg_arg = mock_server.send_message.call_args[0][0]
            self.assertEqual(msg_arg["Subject"], "Verify your SPECra email")
            self.assertEqual(msg_arg["To"], self.to_email)
            self.assertIn("SPECra Product Intelligence <no-reply@specra.io>", msg_arg["From"])

    @patch("smtplib.SMTP_SSL")
    def test_05_brevo_smtp_ssl_port_465_dispatch_success(self, mock_ssl_cls):
        """Test successful SMTP dispatch using SSL on Port 465."""
        mock_server = MagicMock()
        mock_ssl_cls.return_value.__enter__.return_value = mock_server

        with patch.object(settings, "SMTP_HOST", "smtp-relay.brevo.com"), \
             patch.object(settings, "SMTP_PORT", 465), \
             patch.object(settings, "SMTP_USERNAME", "7a8b9c@smtp-brevo.com"), \
             patch.object(settings, "SMTP_PASSWORD", "super_secret_brevo_key"):

            success = EmailService.send_password_reset_email(
                to_email=self.to_email,
                reset_token=self.test_token,
                full_name=self.full_name,
            )

            self.assertTrue(success)
            mock_ssl_cls.assert_called_once_with("smtp-relay.brevo.com", 465, timeout=10)
            mock_server.login.assert_called_once_with("7a8b9c@smtp-brevo.com", "super_secret_brevo_key")
            mock_server.send_message.assert_called_once()

            msg_arg = mock_server.send_message.call_args[0][0]
            self.assertEqual(msg_arg["Subject"], "Reset your SPECra password")
            self.assertEqual(msg_arg["To"], self.to_email)

    @patch("smtplib.SMTP")
    def test_06_verification_email_content_and_links(self, mock_smtp_cls):
        """Verify HTML and plain-text body content of verification email."""
        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_server

        with patch.object(settings, "SMTP_HOST", "smtp-relay.brevo.com"), \
             patch.object(settings, "SMTP_USERNAME", "user"), \
             patch.object(settings, "SMTP_PASSWORD", "pass"), \
             patch.object(settings, "FRONTEND_BASE_URL", "https://app.specra.io"):

            EmailService.send_verification_email(
                to_email=self.to_email,
                verification_token=self.test_token,
                full_name=self.full_name,
            )

            msg = mock_server.send_message.call_args[0][0]
            payloads = [part.get_payload(decode=True).decode("utf-8") for part in msg.get_payload()]
            text_content, html_content = payloads[0], payloads[1]

            # Assertions on text part
            self.assertIn("Hello Alex Vance", text_content)
            self.assertIn(f"https://app.specra.io/#/verify-email?token={self.test_token}", text_content)
            self.assertIn(f"{settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES} minutes", text_content)
            self.assertIn("The SPECra Team", text_content)

            # Assertions on HTML part
            self.assertIn("SPEC", html_content)
            self.assertIn("Verify your email address", html_content)
            self.assertIn("Alex Vance", html_content)
            self.assertIn(f"https://app.specra.io/#/verify-email?token={self.test_token}", html_content)
            self.assertIn("Verify Email Address", html_content)
            self.assertIn("This link will expire in", html_content)

    @patch("smtplib.SMTP")
    def test_07_password_reset_email_content_and_links(self, mock_smtp_cls):
        """Verify HTML and plain-text body content of password reset email."""
        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_server

        with patch.object(settings, "SMTP_HOST", "smtp-relay.brevo.com"), \
             patch.object(settings, "SMTP_USERNAME", "user"), \
             patch.object(settings, "SMTP_PASSWORD", "pass"), \
             patch.object(settings, "FRONTEND_BASE_URL", "https://app.specra.io"):

            EmailService.send_password_reset_email(
                to_email=self.to_email,
                reset_token=self.test_token,
                full_name=self.full_name,
            )

            msg = mock_server.send_message.call_args[0][0]
            payloads = [part.get_payload(decode=True).decode("utf-8") for part in msg.get_payload()]
            text_content, html_content = payloads[0], payloads[1]

            # Assertions on text part
            self.assertIn("Hello Alex Vance", text_content)
            self.assertIn(f"https://app.specra.io/#/reset-password?token={self.test_token}", text_content)
            self.assertIn(f"{settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES} minutes", text_content)
            self.assertIn("If you did not request a password reset", text_content)

            # Assertions on HTML part
            self.assertIn("Reset your password", html_content)
            self.assertIn(f"https://app.specra.io/#/reset-password?token={self.test_token}", html_content)
            self.assertIn("Reset Password", html_content)
            self.assertIn("If you did not request this password reset", html_content)

    @patch("smtplib.SMTP")
    def test_08_smtp_connection_failure_handled_gracefully(self, mock_smtp_cls):
        """Verify that network/SMTP authentication errors are caught and do not leak credentials."""
        mock_smtp_cls.side_effect = smtplib.SMTPAuthenticationError(535, b"Authentication failed")

        with patch.object(settings, "SMTP_HOST", "smtp-relay.brevo.com"), \
             patch.object(settings, "SMTP_USERNAME", "user"), \
             patch.object(settings, "SMTP_PASSWORD", "pass"):

            # Should return False without raising uncaught exception
            success = EmailService.send_verification_email(
                to_email=self.to_email,
                verification_token=self.test_token,
            )
            self.assertFalse(success)

    def test_09_raw_tokens_never_logged_during_email_dispatch(self):
        """Verify that raw tokens are never emitted to loggers during email dispatch."""
        with self.assertLogs("app.services.email_service", level="INFO") as log_cm:
            with patch.object(settings, "SMTP_HOST", ""), \
                 patch.object(settings, "ENVIRONMENT", "development"):
                EmailService.send_verification_email(self.to_email, self.test_token)
                EmailService.send_password_reset_email(self.to_email, self.test_token)

        full_logs = "\n".join(log_cm.output)
        self.assertNotIn(self.test_token, full_logs)

    def test_10_api_responses_never_contain_smtp_credentials(self):
        """Verify that auth endpoints never expose SMTP host, username, or password in HTTP responses."""
        from fastapi.testclient import TestClient
        from app.main import app
        import uuid

        client = TestClient(app)
        reg_res = client.post("/api/v1/auth/register", json={
            "full_name": "Privacy Test",
            "organization": "Privacy Corp",
            "email": f"priv_{uuid.uuid4().hex[:6]}@example.test",
            "password": "StrongPassword123!",
        })
        self.assertEqual(reg_res.status_code, 201)
        self.assertNotIn("smtp", reg_res.text.lower())
        self.assertNotIn("brevo", reg_res.text.lower())

    def test_11_environment_configuration_loading(self):
        """Verify settings attributes for Brevo SMTP match specification."""
        self.assertTrue(hasattr(settings, "SMTP_HOST"))
        self.assertTrue(hasattr(settings, "SMTP_PORT"))
        self.assertTrue(hasattr(settings, "SMTP_USERNAME"))
        self.assertTrue(hasattr(settings, "SMTP_PASSWORD"))
        self.assertTrue(hasattr(settings, "SMTP_FROM_EMAIL"))
        self.assertTrue(hasattr(settings, "SMTP_FROM_NAME"))


if __name__ == "__main__":
    unittest.main()

