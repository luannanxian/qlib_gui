"""
Test Configuration and Fixtures for Database Tests

This module provides pytest fixtures for database testing with async support.
"""

import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.database.base import Base
from app.database.models import Dataset, ChartConfig, UserPreferences
from app.database.repositories import (
    DatasetRepository,
    ChartRepository,
    UserPreferencesRepository,
)


# Test database URL (use in-memory SQLite for testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create a test database engine"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session"""
    async_session = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def dataset_repo(db_session: AsyncSession) -> DatasetRepository:
    """Create a DatasetRepository instance for testing"""
    return DatasetRepository(db_session)


@pytest_asyncio.fixture
async def chart_repo(db_session: AsyncSession) -> ChartRepository:
    """Create a ChartRepository instance for testing"""
    return ChartRepository(db_session)


@pytest_asyncio.fixture
async def user_prefs_repo(db_session: AsyncSession) -> UserPreferencesRepository:
    """Create a UserPreferencesRepository instance for testing"""
    return UserPreferencesRepository(db_session)


@pytest_asyncio.fixture
async def sample_dataset(dataset_repo: DatasetRepository) -> Dataset:
    """Create a sample dataset for testing"""
    dataset_data = {
        "name": "Test Dataset",
        "source": "local",
        "file_path": "/path/to/test.csv",
        "status": "valid",
        "row_count": 1000,
        "columns": ["date", "open", "high", "low", "close", "volume"],
        "metadata": {"description": "Sample test dataset"}
    }
    return await dataset_repo.create(dataset_data)


@pytest_asyncio.fixture
async def sample_chart(chart_repo: ChartRepository, sample_dataset: Dataset) -> ChartConfig:
    """Create a sample chart for testing"""
    chart_data = {
        "name": "Test Chart",
        "chart_type": "kline",
        "dataset_id": sample_dataset.id,
        "config": {
            "x_axis": "date",
            "y_axis": "price",
            "colors": {"up": "green", "down": "red"}
        },
        "description": "Sample test chart"
    }
    return await chart_repo.create(chart_data)


@pytest_asyncio.fixture
async def sample_user_prefs(user_prefs_repo: UserPreferencesRepository) -> UserPreferences:
    """Create sample user preferences for testing"""
    prefs_data = {
        "user_id": "test-user-123",
        "mode": "beginner",
        "language": "en",
        "theme": "light",
        "show_tooltips": True,
        "completed_guides": [],
        "settings": {}
    }
    return await user_prefs_repo.create(prefs_data)
