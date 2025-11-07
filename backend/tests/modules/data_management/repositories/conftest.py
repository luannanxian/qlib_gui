"""
Pytest Configuration for Repository Tests

Provides fixtures for repository layer tests using SQLite in-memory database.
"""

import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker, AsyncEngine
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.database.models import (
    IndicatorComponent, CustomFactor, UserFactorLibrary, FactorValidationResult,
    Dataset, ChartConfig, UserPreferences, ImportTask,
    DataPreprocessingRule, DataPreprocessingTask,
    StrategyTemplate, StrategyInstance, TemplateRating
)
from app.database.repositories.import_task import ImportTaskRepository

# Use SQLite in-memory database for fast testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="function")
def event_loop():
    """Create an event loop for each test function"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create a test database engine"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},  # Required for SQLite
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
async def db_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
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
async def import_task_repo(db_session: AsyncSession) -> ImportTaskRepository:
    """Create an ImportTaskRepository instance for testing"""
    return ImportTaskRepository(db_session)
