"""
Pytest Configuration for Indicator Tests

Provides fixtures for testing indicator functionality.
"""

import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.database.base import Base
# Import all models to register them with Base.metadata
from app.database.models import (
    Dataset, ChartConfig, UserPreferences, ImportTask,
    IndicatorComponent, CustomFactor, FactorValidationResult, UserFactorLibrary
)
from app.database.repositories.indicator_repository import IndicatorRepository
from app.database.repositories.custom_factor_repository import CustomFactorRepository
from app.database.repositories.factor_validation_repository import FactorValidationResultRepository
from app.database.repositories.user_factor_library_repository import UserFactorLibraryRepository

# Test database URL (use file-based SQLite for testing to avoid in-memory issues)
import tempfile
import os
TEST_DB_FILE = os.path.join(tempfile.gettempdir(), "test_indicator.db")
TEST_DATABASE_URL = f"sqlite+aiosqlite:///{TEST_DB_FILE}"


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create a test database engine"""
    # Remove existing test database if present
    if os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)

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

    # Clean up database file
    if os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)


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
async def indicator_repo(db_session: AsyncSession) -> IndicatorRepository:
    """Create an IndicatorRepository instance for testing"""
    return IndicatorRepository(db_session)


@pytest_asyncio.fixture
async def custom_factor_repo(db_session: AsyncSession) -> CustomFactorRepository:
    """Create a CustomFactorRepository instance for testing"""
    return CustomFactorRepository(db_session)


@pytest_asyncio.fixture
async def factor_validation_repo(db_session: AsyncSession) -> FactorValidationResultRepository:
    """Create a FactorValidationResultRepository instance for testing"""
    return FactorValidationResultRepository(db_session)


@pytest_asyncio.fixture
async def user_library_repo(db_session: AsyncSession) -> UserFactorLibraryRepository:
    """Create a UserFactorLibraryRepository instance for testing"""
    return UserFactorLibraryRepository(db_session)
