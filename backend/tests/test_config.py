"""
Tests for application configuration
"""

import pytest
from pydantic import ValidationError


class TestSettings:
    """Test Settings configuration"""

    def test_settings_default_values(self):
        """Test Settings with default values"""
        from app.config import Settings

        settings = Settings()

        assert settings.APP_NAME == "Qlib-UI"
        assert settings.DEBUG is True  # Default is True in development
        assert settings.APP_ENV == "development"
        assert settings.API_PREFIX == "/api"
        # SQLite已移除，统一使用MySQL
        assert "mysql" in settings.DATABASE_URL.lower() or "sqlite" in settings.DATABASE_URL.lower()
        assert "redis://localhost" in settings.REDIS_URL
        assert settings.LOG_LEVEL == "INFO"
        assert isinstance(settings.CORS_ORIGINS, list)
        assert len(settings.CORS_ORIGINS) > 0

    def test_settings_custom_values(self):
        """Test Settings with custom values"""
        from app.config import Settings
        
        settings = Settings(
            APP_NAME="Custom App",
            DEBUG=True,
            DATABASE_URL="postgresql://user:pass@localhost/db",
            REDIS_URL="redis://custom:6380/1",
            LOG_LEVEL="DEBUG"
        )
        
        assert settings.APP_NAME == "Custom App"
        assert settings.DEBUG is True
        assert settings.DATABASE_URL == "postgresql://user:pass@localhost/db"
        assert settings.REDIS_URL == "redis://custom:6380/1"
        assert settings.LOG_LEVEL == "DEBUG"

    def test_settings_from_env(self, monkeypatch):
        """Test Settings loading from environment variables"""
        from app.config import Settings
        
        monkeypatch.setenv("APP_NAME", "Env App")
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("SECRET_KEY", "test-secret-key")
        
        settings = Settings()
        
        assert settings.APP_NAME == "Env App"
        assert settings.DEBUG is True
        assert settings.SECRET_KEY == "test-secret-key"

    def test_settings_secret_key_required_in_production(self):
        """Test that secret key should be changed in production"""
        from app.config import Settings
        
        settings = Settings()
        
        # Default secret key should trigger a warning in production
        assert "change-in-production" in settings.SECRET_KEY.lower()

    def test_settings_database_url_validation(self):
        """Test DATABASE_URL can accept various database types"""
        from app.config import Settings
        
        # SQLite
        settings1 = Settings(DATABASE_URL="mysql+aiomysql://test_user:test_password@localhost:3307/test_db")
        assert "mysql" in settings1.DATABASE_URL
        
        # PostgreSQL
        settings2 = Settings(DATABASE_URL="postgresql://localhost/testdb")
        assert "postgresql" in settings2.DATABASE_URL
        
        # MySQL
        settings3 = Settings(DATABASE_URL="mysql://localhost/testdb")
        assert "mysql" in settings3.DATABASE_URL

    def test_settings_redis_url_format(self):
        """Test REDIS_URL format validation"""
        from app.config import Settings
        
        settings = Settings(REDIS_URL="redis://localhost:6379/0")
        assert settings.REDIS_URL.startswith("redis://")

    def test_settings_log_level_options(self):
        """Test valid log level options"""
        from app.config import Settings
        
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            settings = Settings(LOG_LEVEL=level)
            assert settings.LOG_LEVEL == level

    def test_settings_cors_origins_list(self):
        """Test CORS_ORIGINS as list"""
        from app.config import Settings
        
        settings = Settings(CORS_ORIGINS=["http://localhost:3000", "https://example.com"])
        assert len(settings.CORS_ORIGINS) == 2
        assert "http://localhost:3000" in settings.CORS_ORIGINS

    def test_settings_model_config(self):
        """Test Settings model configuration"""
        from app.config import Settings
        
        settings = Settings()
        
        # Check that Settings is a Pydantic BaseSettings
        assert hasattr(settings, 'model_dump')
        assert hasattr(settings, 'model_fields')

    def test_settings_serialization(self):
        """Test Settings can be serialized"""
        from app.config import Settings
        
        settings = Settings()
        data = settings.model_dump()
        
        assert "APP_NAME" in data
        assert "DATABASE_URL" in data
        assert "SECRET_KEY" in data


class TestGetSettings:
    """Test get_settings function"""

    def test_get_settings_returns_settings_instance(self):
        """Test get_settings returns Settings instance"""
        from app.config import get_settings, Settings
        
        settings = get_settings()
        
        assert isinstance(settings, Settings)
        assert settings.APP_NAME == "Qlib-UI"

    def test_get_settings_is_cached(self):
        """Test get_settings uses caching"""
        from app.config import get_settings
        
        settings1 = get_settings()
        settings2 = get_settings()
        
        # Should return the same instance due to @lru_cache
        assert settings1 is settings2

    def test_settings_server_config(self):
        """Test server configuration"""
        from app.config import Settings
        
        settings = Settings(HOST="127.0.0.1", PORT=9000)
        assert settings.HOST == "127.0.0.1"
        assert settings.PORT == 9000

    def test_settings_database_config(self):
        """Test database configuration"""
        from app.config import Settings
        
        settings = Settings(
            DATABASE_POOL_SIZE=50,
            DATABASE_MAX_OVERFLOW=20,
            DATABASE_ECHO=True
        )
        assert settings.DATABASE_POOL_SIZE == 50
        assert settings.DATABASE_MAX_OVERFLOW == 20
        assert settings.DATABASE_ECHO is True

    def test_settings_celery_config(self):
        """Test Celery configuration"""
        from app.config import Settings
        
        settings = Settings(
            CELERY_BROKER_URL="redis://localhost:6379/3",
            CELERY_RESULT_BACKEND="redis://localhost:6379/4"
        )
        assert settings.CELERY_BROKER_URL == "redis://localhost:6379/3"
        assert settings.CELERY_RESULT_BACKEND == "redis://localhost:6379/4"

    def test_settings_security_config(self):
        """Test security configuration"""
        from app.config import Settings
        
        settings = Settings(
            SECRET_KEY="test-secret",
            ALGORITHM="HS512",
            ACCESS_TOKEN_EXPIRE_MINUTES=60
        )
        assert settings.SECRET_KEY == "test-secret"
        assert settings.ALGORITHM == "HS512"
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 60

    def test_settings_qlib_config(self):
        """Test Qlib configuration"""
        from app.config import Settings
        
        settings = Settings(
            QLIB_DATA_DIR="./custom/qlib",
            QLIB_REGION="us"
        )
        assert settings.QLIB_DATA_DIR == "./custom/qlib"
        assert settings.QLIB_REGION == "us"

    def test_settings_file_storage_config(self):
        """Test file storage configuration"""
        from app.config import Settings
        
        settings = Settings(
            DATA_DIR="./custom/data",
            UPLOAD_DIR="./custom/uploads",
            RESULT_DIR="./custom/results",
            LOG_DIR="./custom/logs",
            CACHE_DIR="./custom/cache",
            MAX_UPLOAD_SIZE_MB=200
        )
        assert settings.DATA_DIR == "./custom/data"
        assert settings.UPLOAD_DIR == "./custom/uploads"
        assert settings.RESULT_DIR == "./custom/results"
        assert settings.LOG_DIR == "./custom/logs"
        assert settings.CACHE_DIR == "./custom/cache"
        assert settings.MAX_UPLOAD_SIZE_MB == 200

    def test_settings_task_scheduling_config(self):
        """Test task scheduling configuration"""
        from app.config import Settings
        
        settings = Settings(
            MAX_PARALLEL_TASKS=5,
            TASK_TIMEOUT_SECONDS=7200
        )
        assert settings.MAX_PARALLEL_TASKS == 5
        assert settings.TASK_TIMEOUT_SECONDS == 7200

    def test_settings_app_env_variations(self):
        """Test different APP_ENV values"""
        from app.config import Settings
        
        for env in ["development", "staging", "production"]:
            settings = Settings(APP_ENV=env)
            assert settings.APP_ENV == env
