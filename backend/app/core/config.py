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

    # Authentication & Security Configuration
    AUTH_SECRET: str = "specra-development-secret-key-change-in-production-32bytes"
    SESSION_EXPIRE_HOURS: int = 24 * 7  # 7 days session lifetime
    COOKIE_NAME: str = "specra_session"
    COOKIE_SECURE: bool = False  # Set to True in production HTTPS
    COOKIE_SAMESITE: str = "lax"

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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
