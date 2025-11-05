"""
Pytest Configuration for Strategy API Tests

Provides fixtures for testing strategy API endpoints with proper async database setup.
"""

import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import patch, MagicMock, AsyncMock

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
# Import all models to register them with Base.metadata
from app.database.models import (
    Dataset, ChartConfig, UserPreferences, ImportTask,
    DataPreprocessingRule, DataPreprocessingTask,
    StrategyTemplate, StrategyInstance, TemplateRating
)
from app.database.repositories.strategy_template import StrategyTemplateRepository
from app.database.repositories.strategy_instance import StrategyInstanceRepository
from app.database.repositories.template_rating import TemplateRatingRepository
from app.database import get_db

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
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
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
async def template_repo(db_session: AsyncSession) -> StrategyTemplateRepository:
    """Create a StrategyTemplateRepository instance for testing"""
    return StrategyTemplateRepository(db_session)


@pytest_asyncio.fixture
async def instance_repo(db_session: AsyncSession) -> StrategyInstanceRepository:
    """Create a StrategyInstanceRepository instance for testing"""
    return StrategyInstanceRepository(db_session)


@pytest_asyncio.fixture
async def rating_repo(db_session: AsyncSession) -> TemplateRatingRepository:
    """Create a TemplateRatingRepository instance for testing"""
    return TemplateRatingRepository(db_session)


@pytest.fixture
def client(event_loop) -> Generator[TestClient, None, None]:
    """Create test client with overridden database dependency.

    This fixture creates its own test engine and session, properly configured
    to use an in-memory SQLite database for isolation and speed.
    """
    # Create test engine and session using event_loop
    engine = event_loop.run_until_complete(_create_test_engine())
    session = event_loop.run_until_complete(_create_test_session(engine))

    from app.main import app
    from app.database import db_manager

    # Reset db_manager to uninitialized state (clear any existing production database)
    db_manager._engine = None
    db_manager._sessionmaker = None

    # Patch db_manager.init() BEFORE creating TestClient to intercept app startup
    original_init = db_manager.init
    original_close = db_manager.close

    def mock_init():
        """Mock init that configures test database"""
        db_manager._engine = engine
        db_manager._sessionmaker = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

    def mock_close():
        """Mock close to prevent closing our test engine"""
        pass

    db_manager.init = mock_init
    db_manager.close = mock_close

    # Override the get_db dependency with our test session
    def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        """Override dependency that returns test session"""
        try:
            yield session
        finally:
            pass

    # Set the override
    app.dependency_overrides[get_db] = override_get_db

    try:
        # Create and yield the test client (this triggers app startup/lifespan)
        with TestClient(app) as test_client:
            yield test_client
    finally:
        # Clean up
        app.dependency_overrides.clear()
        db_manager.init = original_init
        db_manager.close = original_close
        event_loop.run_until_complete(_cleanup_session(session))
        event_loop.run_until_complete(_cleanup_engine(engine))


async def _create_test_engine():
    """Helper to create test engine with tables"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
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
