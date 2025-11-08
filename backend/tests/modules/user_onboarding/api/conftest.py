"""
Pytest configuration for User Onboarding API tests.
"""

import asyncio
import os
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker, AsyncEngine
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.database.models import UserPreferences
from app.main import app

# Load test environment variables
load_dotenv(".env.test")

# Get database URL from environment variable
# Default to SQLite in-memory for fast testing
TEST_DATABASE_URL = os.getenv(
    "DATABASE_URL_TEST",
    "sqlite+aiosqlite:///:memory:"
)

IS_SQLITE = "sqlite" in TEST_DATABASE_URL
IS_MYSQL = "mysql" in TEST_DATABASE_URL


@pytest.fixture(scope="session")
def event_loop():
    """
    Create an event loop for the test session.

    This ensures all async tests share the same event loop,
    which is necessary for proper async fixture handling.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


def get_engine_config():
    """
    Get database engine configuration based on database type.

    Returns:
        dict: Engine configuration parameters
    """
    if IS_SQLITE:
        return {
            "url": TEST_DATABASE_URL,
            "echo": False,
            "poolclass": StaticPool,
            "connect_args": {
                "check_same_thread": False,
            }
        }
    elif IS_MYSQL:
        return {
            "url": TEST_DATABASE_URL,
            "echo": False,
            "pool_size": 5,
            "max_overflow": 5,
            "pool_recycle": 1800,
            "pool_pre_ping": True,
            "pool_timeout": 30,
            "connect_args": {
                "charset": "utf8mb4",
                "autocommit": False,
            },
        }
    else:
        raise ValueError(f"Unsupported database URL: {TEST_DATABASE_URL}")


@pytest_asyncio.fixture(scope="function")
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """
    Create a test database engine.

    Lifecycle:
    - Function scope: New engine for each test function
    - Creates all tables before test
    - Drops all tables after test

    Yields:
        AsyncEngine: Configured async database engine
    """
    engine_config = get_engine_config()
    engine = create_async_engine(**engine_config)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    # Dispose engine and close all connections
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a test database session.

    Lifecycle:
    - Function scope: New session for each test function
    - Automatically rolls back after test for isolation

    Yields:
        AsyncSession: Configured async database session
    """
    async_session = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with async_session() as session:
        yield session
        # Rollback any uncommitted changes
        await session.rollback()


@pytest.fixture
def client():
    """Create test client for FastAPI application"""
    return TestClient(app)


@pytest.fixture
def mock_audit_logger():
    """
    Mock AuditLogger for testing.

    Returns:
        MagicMock: Mocked audit logger
    """
    mock_logger = MagicMock()
    mock_logger.log_event = AsyncMock()
    return mock_logger
