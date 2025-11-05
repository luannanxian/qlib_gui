"""
Application Configuration
"""

from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator, ValidationError
import re
import sys


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    APP_NAME: str = "Qlib-UI"
    APP_ENV: str = Field(default="development", env="APP_ENV")
    DEBUG: bool = Field(default=True, env="DEBUG")
    API_PREFIX: str = "/api"

    # Server
    BACKEND_HOST: str = Field(default="0.0.0.0")
    BACKEND_PORT: int = Field(default=8000)

    # Database - MySQL Configuration
    # IMPORTANT: Never commit real credentials! Set via DATABASE_URL environment variable
    DATABASE_URL: str = Field(
        ...,  # Required field, no default
        env="DATABASE_URL",
        description="Database connection URL (e.g., mysql+aiomysql://user:pass@host:port/db)"
    )
    DATABASE_POOL_SIZE: int = Field(default=20, env="DATABASE_POOL_SIZE")
    DATABASE_MAX_OVERFLOW: int = Field(default=10, env="DATABASE_MAX_OVERFLOW")
    DATABASE_ECHO: bool = Field(default=False, env="DATABASE_ECHO")
    DATABASE_POOL_RECYCLE: int = Field(default=3600, env="DATABASE_POOL_RECYCLE")  # Recycle connections after 1 hour
    DATABASE_POOL_PRE_PING: bool = Field(default=True, env="DATABASE_POOL_PRE_PING")  # Verify connections before use

    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")

    # Celery
    CELERY_BROKER_URL: str = Field(
        default="redis://localhost:6379/1",
        env="CELERY_BROKER_URL"
    )
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://localhost:6379/2",
        env="CELERY_RESULT_BACKEND"
    )

    # Security
    SECRET_KEY: str = Field(
        ...,  # Required field, no default
        env="SECRET_KEY",
        min_length=32,
        description="Secret key for JWT signing (min 32 chars, use 64+ in production)"
    )
    ALGORITHM: str = Field(default="HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")

    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        env="CORS_ORIGINS"
    )

    # Qlib
    QLIB_DATA_DIR: str = Field(default="./data/qlib", env="QLIB_DATA_DIR")
    QLIB_REGION: str = Field(default="cn", env="QLIB_REGION")

    # File Storage
    DATA_DIR: str = Field(default="./data", env="DATA_DIR")
    UPLOAD_DIR: str = Field(default="./data/uploads", env="UPLOAD_DIR")
    RESULT_DIR: str = Field(default="./results", env="RESULT_DIR")
    LOG_DIR: str = Field(default="./logs", env="LOG_DIR")
    CACHE_DIR: str = Field(default="./cache", env="CACHE_DIR")

    MAX_UPLOAD_SIZE_MB: int = Field(default=100, env="MAX_UPLOAD_SIZE_MB")

    # Task Scheduling
    MAX_PARALLEL_TASKS: int = Field(default=2, env="MAX_PARALLEL_TASKS")
    TASK_TIMEOUT_SECONDS: int = Field(default=3600, env="TASK_TIMEOUT_SECONDS")

    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(default="json", env="LOG_FORMAT")  # json or text
    LOG_ROTATION_SIZE: str = Field(default="100 MB", env="LOG_ROTATION_SIZE")
    LOG_RETENTION_DAYS: int = Field(default=30, env="LOG_RETENTION_DAYS")
    LOG_COMPRESSION: str = Field(default="zip", env="LOG_COMPRESSION")
    LOG_REQUEST_BODY: bool = Field(default=True, env="LOG_REQUEST_BODY")
    LOG_RESPONSE_BODY: bool = Field(default=False, env="LOG_RESPONSE_BODY")
    SLOW_QUERY_THRESHOLD_MS: float = Field(default=100.0, env="SLOW_QUERY_THRESHOLD_MS")
    SLOW_REQUEST_THRESHOLD_MS: float = Field(default=1000.0, env="SLOW_REQUEST_THRESHOLD_MS")

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL for security issues"""
        # Check for weak/common passwords
        weak_passwords = ["password", "123456", "admin", "root", "test"]

        # Extract password from URL
        if "@" in v:
            credentials_part = v.split("@")[0]
            if ":" in credentials_part:
                password = credentials_part.split(":")[-1].split("//")[-1]

                # Check password strength
                if password.lower() in weak_passwords:
                    raise ValueError(
                        "Weak database password detected! Use a strong password with "
                        "at least 12 characters including letters, numbers, and symbols."
                    )

                if len(password) < 8:
                    raise ValueError(
                        "Database password too short! Use at least 8 characters "
                        "(12+ recommended for production)."
                    )

        return v

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        """Validate SECRET_KEY strength especially in production"""
        # Get environment from values being validated
        app_env = info.data.get("APP_ENV", "development")

        # Check for default/weak secret keys
        weak_keys = [
            "secret",
            "your-secret-key",
            "change-me",
            "insecure",
            "dev-secret",
        ]

        if any(weak in v.lower() for weak in weak_keys):
            raise ValueError(
                "Weak SECRET_KEY detected! Generate a secure random key using: "
                "python -c 'import secrets; print(secrets.token_urlsafe(64))'"
            )

        # Enforce stronger requirements in production
        if app_env == "production":
            if len(v) < 64:
                raise ValueError(
                    "SECRET_KEY must be at least 64 characters in production! "
                    "Generate one using: python -c 'import secrets; print(secrets.token_urlsafe(64))'"
                )

            # Check entropy (should have mixed characters)
            if not (any(c.isupper() for c in v) or any(c.islower() for c in v)):
                raise ValueError("SECRET_KEY must contain mixed case characters for production")

        return v

    def validate_required_vars(self) -> None:
        """
        Validate required environment variables at application startup.

        This method checks that all critical environment variables are properly set
        and provides helpful error messages for missing or invalid configurations.

        Raises:
            ValueError: If any critical environment variable is missing or invalid
        """
        errors = []

        # Check DATABASE_URL
        if not self.DATABASE_URL:
            errors.append("DATABASE_URL is required but not set")
        elif not any(self.DATABASE_URL.startswith(prefix) for prefix in ["mysql+aiomysql://", "mysql+pymysql://", "postgresql+asyncpg://"]):
            errors.append(
                "DATABASE_URL must start with a valid async driver: "
                "mysql+aiomysql://, mysql+pymysql://, or postgresql+asyncpg://"
            )

        # Check SECRET_KEY
        if not self.SECRET_KEY:
            errors.append("SECRET_KEY is required but not set")

        # Check Redis URLs
        if not self.REDIS_URL.startswith("redis://"):
            errors.append("REDIS_URL must start with redis://")

        if not self.CELERY_BROKER_URL.startswith("redis://"):
            errors.append("CELERY_BROKER_URL must start with redis://")

        if not self.CELERY_RESULT_BACKEND.startswith("redis://"):
            errors.append("CELERY_RESULT_BACKEND must start with redis://")

        # Check directory paths exist or can be created
        import os
        for dir_name, dir_path in [
            ("DATA_DIR", self.DATA_DIR),
            ("UPLOAD_DIR", self.UPLOAD_DIR),
            ("RESULT_DIR", self.RESULT_DIR),
            ("LOG_DIR", self.LOG_DIR),
            ("CACHE_DIR", self.CACHE_DIR),
        ]:
            try:
                os.makedirs(dir_path, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create {dir_name} at {dir_path}: {e}")

        # Production-specific checks
        if self.APP_ENV == "production":
            if self.DEBUG:
                errors.append("DEBUG must be False in production")

            if len(self.SECRET_KEY) < 64:
                errors.append("SECRET_KEY must be at least 64 characters in production")

            if "localhost" in self.DATABASE_URL or "127.0.0.1" in self.DATABASE_URL:
                errors.append(
                    "DATABASE_URL should not use localhost in production. "
                    "Use proper database host."
                )

        if errors:
            error_message = "Environment variable validation failed:\n" + "\n".join(f"  - {error}" for error in errors)
            raise ValueError(error_message)

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Get settings instance with caching.
    This function is cached to avoid re-reading environment variables.
    """
    return Settings()


# Global settings instance for convenience
settings = get_settings()
