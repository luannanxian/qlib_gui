"""
Pytest Configuration for Indicator API Tests

Provides fixtures for testing indicator API endpoints with proper async database setup.
"""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio

# Import fixtures from parent conftest files
# This is the new way to share fixtures without using pytest_plugins
# The fixtures from conftest.py in parent directories are automatically discovered
from tests.modules.indicator.repositories.conftest import *
from tests.modules.indicator.services.conftest import *
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.database.base import Base
# Import all models to register them with Base.metadata
from app.database.models import (
    IndicatorComponent, CustomFactor, UserFactorLibrary, FactorValidationResult,
    Dataset, ChartConfig, UserPreferences, ImportTask,
    DataPreprocessingRule, DataPreprocessingTask,
    StrategyTemplate, StrategyInstance, TemplateRating
)
from app.database.repositories.indicator_repository import IndicatorRepository
from app.database.repositories.custom_factor_repository import CustomFactorRepository
from app.database.repositories.user_factor_library_repository import UserFactorLibraryRepository
from app.database import get_db

# Test database URL (use in-memory SQLite for testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


# The async_client fixture is already provided by the inherited fixtures
# but we need to override it to use the API test configuration

@pytest_asyncio.fixture(scope="function")
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create an async HTTP client with database dependency override.

    This approach uses httpx.AsyncClient instead of TestClient to avoid
    lifecycle issues with async SQLAlchemy table creation.
    """
    from app.main import app
    from httpx import ASGITransport

    # Override the get_db dependency
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # Create async client with ASGI transport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    # Clean up
    app.dependency_overrides.clear()
