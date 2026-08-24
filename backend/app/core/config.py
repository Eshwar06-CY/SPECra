"""
Core configurations and settings for Deadlock backend.
"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Deadlock"
    DESCRIPTION: str = "AI-Powered Industrial Product Intelligence Engine"
    VERSION: str = "0.1.0"
    API_PREFIX: str = "/api/v1"
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    # Environment & Transport Security
    ENVIRONMENT: str = "development"  # "development", "test", or "production"
    ENABLE_HSTS: bool = False  # Keep False on localhost; set True or ENVIRONMENT=production for HSTS
    HSTS_MAX_AGE: int = 31536000  # 1 year in seconds
    HSTS_INCLUDE_SUBDOMAINS: bool = True
    HSTS_PRELOAD: bool = False
    MAX_REQUEST_BODY_SIZE_MB: int = 50

    # Authentication & Security Configuration
    AUTH_SECRET: str = "specra-development-secret-key-change-in-production-32bytes"
    SESSION_EXPIRE_HOURS: int = 24 * 7  # 7 days session lifetime
    COOKIE_NAME: str = "specra_session"
    COOKIE_SECURE: bool = False  # Set to True in production HTTPS
    COOKIE_SAMESITE: str = "lax"
    MAX_LOGIN_ATTEMPTS: int = 5  # Lock out after 5 consecutive failed attempts
    LOGIN_LOCKOUT_SECONDS: int = 300  # 5 minutes lockout duration
    EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES: int = 60  # 60 minutes verification token lifetime
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30  # 30 minutes password reset token lifetime

    # Database Configuration
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/deadlock"
    
    # File Storage / Ingestion Configuration
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 50

    # Google Gemini AI Configuration (Primary & Dedicated)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.7-flash"
    GEMINI_MAX_CONCURRENCY: int = 5
    GEMINI_REQUEST_TIMEOUT: float = 30.0
    GEMINI_MAX_RETRIES: int = 3

    # Brevo / SMTP Email Delivery Configuration
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "no-reply@specra.io"
    SMTP_FROM_NAME: str = "SPECra Product Intelligence"
    SMTP_USE_TLS: bool = True
    FRONTEND_BASE_URL: str = "http://localhost:5173"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    def validate_production_environment(self):
        """
        Validates environment configuration when running in production mode.
        Raises ValueError if weak/default secrets, placeholder values, or wildcard CORS are detected.
        """
        if self.ENVIRONMENT.lower() != "production":
            return

        insecure_secrets = [
            "specra-development-secret-key-change-in-production-32bytes",
            "specra-production-secret-key-change-in-prod-env-32b",
            "CHANGE_ME_TO_A_CRYPTOGRAPHICALLY_SECURE_64_BYTE_RANDOM_SECRET",
            "secret",
            "password",
            "changeme",
        ]

        if self.AUTH_SECRET in insecure_secrets or len(self.AUTH_SECRET) < 32:
            raise ValueError(
                "CRITICAL SECURITY CONFIGURATION ERROR: In production mode, AUTH_SECRET must be set "
                "to a cryptographically secure random secret of at least 32 characters."
            )

        if "*" in self.CORS_ORIGINS:
            raise ValueError(
                "CRITICAL SECURITY CONFIGURATION ERROR: Wildcard CORS ('*') is strictly forbidden in production."
            )


settings = Settings()
