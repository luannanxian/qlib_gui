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
from sqlalchemy.pool import NullPool, StaticPool
from sqlalchemy import text
from httpx import AsyncClient

from app.database.base import Base
# Import all models to register them with Base.metadata
from app.database.models import (
    Dataset, ChartConfig, UserPreferences, ImportTask,
    DataPreprocessingRule, DataPreprocessingTask
)
from app.database.repositories.dataset import DatasetRepository
from app.database import get_db

# Use SQLite in-memory database for fast testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="function")
def event_loop():
    """Create an event loop for each test function"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_engine_session():
    """
    Create a function-level test database engine with optimized pooling.

    Uses StaticPool for single-connection pooling, which is ideal for testing.
    Tables are created once per test function and dropped at the end.

    Note: Using function scope to avoid event loop conflicts between tests.
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=StaticPool,  # Single connection pool for testing
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
async def test_engine(event_loop):
    """
    DEPRECATED: Use test_engine_session instead.

    Kept for backward compatibility with existing tests.
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
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
async def db_session(test_engine_session) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a test database session with transaction isolation.

    Each test runs in its own transaction which is automatically rolled back
    after the test completes. This ensures test isolation without needing to
    manually clean up data.

    Uses test_engine_session (session-scoped) for connection reuse.
    """
    # Create a connection from the session-level engine
    async with test_engine_session.connect() as conn:
        # Start a transaction
        async with conn.begin() as trans:
            # Create a session bound to this connection
            session = AsyncSession(
                bind=conn,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )

            yield session

            # Rollback the transaction after test
            # This ensures all changes are discarded
            await trans.rollback()


@pytest_asyncio.fixture
async def dataset_repo(db_session: AsyncSession) -> DatasetRepository:
    """Create a DatasetRepository instance for testing"""
    return DatasetRepository(db_session)


@pytest_asyncio.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create async HTTP client for testing FastAPI endpoints.

    This fixture provides a fully async HTTP client that works seamlessly
    with async database sessions, avoiding event loop conflicts.

    IMPORTANT: Shares the same db_session to ensure transaction isolation works.
    """
    from app.main import app
    from httpx import ASGITransport

    # Override the get_db dependency to use the shared db_session
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        """Override dependency that returns the shared test session"""
        yield db_session

    # Set the override
    app.dependency_overrides[get_db] = override_get_db

    try:
        # Create async HTTP client with ASGI transport
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            yield client
    finally:
        # Clean up
        app.dependency_overrides.clear()


@pytest.fixture
def client(event_loop) -> Generator[TestClient, None, None]:
    """
    DEPRECATED: Use async_client instead.

    Synchronous test client kept for backward compatibility.
    This client has event loop conflicts with async db_session.
    """
    from app.main import app

    # Create engine for this test
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
        connect_args={"check_same_thread": False},  # Required for SQLite
    )

    # Create tables synchronously
    async def setup_db():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    event_loop.run_until_complete(setup_db())

    # Override the get_db dependency
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        """Override dependency that returns test session"""
        async_session = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
        async with async_session() as session:
            yield session
            await session.rollback()

    # Set the override
    app.dependency_overrides[get_db] = override_get_db

    try:
        # Create and yield the test client
        with TestClient(app) as test_client:
            yield test_client
    finally:
        # Clean up
        app.dependency_overrides.clear()

        # Drop tables
        async def cleanup_db():
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            await engine.dispose()

        event_loop.run_until_complete(cleanup_db())


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
        connect_args={"check_same_thread": False},  # Required for SQLite
    )

    # Debug: Print tables before creation
    print(f"DEBUG: Tables in metadata before create_all: {list(Base.metadata.tables.keys())}")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # Debug: Verify tables were created (MySQL version)
        result = await conn.execute(text("SHOW TABLES;"))
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
