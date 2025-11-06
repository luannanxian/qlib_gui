"""
Pytest Configuration for Dataset API Tests

Provides fixtures for testing dataset API endpoints with proper async database setup.
"""

import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import patch, MagicMock, AsyncMock

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import text

from app.database.base import Base
# Import all models to register them with Base.metadata
from app.database.models import (
    Dataset, ChartConfig, UserPreferences, ImportTask,
    DataPreprocessingRule, DataPreprocessingTask
)
from app.database.repositories.dataset import DatasetRepository
from app.database import get_db

# Test database URL (use in-memory SQLite for testing)
TEST_DATABASE_URL = "mysql+aiomysql://remote:remote123456@192.168.3.46:3306/qlib_ui_test?charset=utf8mb4"


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


@pytest.fixture
def client(db_session: AsyncSession, event_loop) -> Generator[TestClient, None, None]:
    """Create test client with overridden database dependency.

    Uses the db_session fixture to ensure consistent database state.
    """
    from app.main import app

    # Override the get_db dependency with our test session
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        """Override dependency that returns test session"""
        yield db_session

    # Set the override
    app.dependency_overrides[get_db] = override_get_db

    try:
        # Create and yield the test client
        # Note: We set raise_server_exceptions=False to avoid issues with lifespan
        with TestClient(app) as test_client:
            yield test_client
    finally:
        # Clean up
        app.dependency_overrides.clear()


async def _create_test_engine():
    """Helper to create test engine with tables"""
    # Ensure all models are imported before creating tables
    from app.database.models import (
        Dataset, ChartConfig, UserPreferences, ImportTask,
        DataPreprocessingRule, DataPreprocessingTask
    )

    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )

    # Debug: Print tables before creation
    print(f"DEBUG: Tables in metadata before create_all: {list(Base.metadata.tables.keys())}")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # Debug: Verify tables were created
        result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
        created_tables = [row[0] for row in result]
        print(f"DEBUG: Tables actually created in DB: {created_tables}")

    return engine


async def _create_test_session(engine):
    """Helper to create test session"""
    async_session = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    return async_session()


async def _cleanup_session(session: AsyncSession):
    """Helper to cleanup session"""
    try:
        await session.rollback()
        await session.close()
    except Exception:
        pass


async def _cleanup_engine(engine):
    """Helper to cleanup engine"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    except Exception:
        pass
    finally:
        await engine.dispose()
