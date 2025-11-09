"""
Pytest Configuration for Strategy Tests

Provides fixtures for testing strategy functionality.
"""

import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

# Import all models FIRST to register them with Base.metadata
from app.database.models import (
    Dataset,
    ChartConfig,
    UserPreferences,
    ImportTask,
    DataPreprocessingRule,
    DataPreprocessingTask,
    StrategyTemplate,
    StrategyInstance,
    TemplateRating,
    NodeTemplate,
    QuickTest,
    CodeGeneration,
    BuilderSession,
)
from app.database.base import Base

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
    # Use StaticPool to ensure the same connection is reused for in-memory database
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=StaticPool,
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
