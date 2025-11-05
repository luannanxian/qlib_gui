"""
Application Configuration
"""

from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    APP_NAME: str = "Qlib-UI"
    APP_ENV: str = Field(default="development", env="APP_ENV")
    DEBUG: bool = Field(default=True, env="DEBUG")
    API_PREFIX: str = "/api"

    # Server
    HOST: str = Field(default="0.0.0.0", env="BACKEND_HOST")
    PORT: int = Field(default=8000, env="BACKEND_PORT")

    # Database
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./qlib_ui.db",
        env="DATABASE_URL"
    )
    DATABASE_POOL_SIZE: int = Field(default=20, env="DATABASE_POOL_SIZE")
    DATABASE_MAX_OVERFLOW: int = Field(default=10, env="DATABASE_MAX_OVERFLOW")
    DATABASE_ECHO: bool = Field(default=False, env="DATABASE_ECHO")

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
        default="your-secret-key-change-in-production",
        env="SECRET_KEY"
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
