"""
Pytest configuration for Repository layer tests.

Supports both SQLite (fast local testing) and MySQL (integration testing).
Database selection controlled by DATABASE_URL_TEST environment variable.

Environment Setup:
    1. SQLite (default, fast):
       export DATABASE_URL_TEST=sqlite+aiosqlite:///:memory:

    2. MySQL (integration testing):
       export DATABASE_URL_TEST=mysql+aiomysql://test_user:test_password@localhost:3307/qlib_ui_test

Usage:
    # Run with SQLite (default)
    pytest tests/modules/indicator/repositories/

    # Run with MySQL
    docker-compose -f docker-compose.test.yml up -d
    export DATABASE_URL_TEST=mysql+aiomysql://test_user:test_password@localhost:3307/qlib_ui_test
    pytest tests/modules/indicator/repositories/
"""

import asyncio
import os
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker, AsyncEngine
from sqlalchemy.pool import StaticPool, QueuePool

from app.database.base import Base
# Import all models to register them with Base.metadata
from app.database.models import (
    IndicatorComponent, CustomFactor, UserFactorLibrary, FactorValidationResult,
    Dataset, ChartConfig, UserPreferences, ImportTask,
    DataPreprocessingRule, DataPreprocessingTask,
    StrategyTemplate, StrategyInstance, TemplateRating
)

# Load test environment variables
load_dotenv(".env.test")

# Get database URL from environment variable
# Default to SQLite in-memory for fast testing
TEST_DATABASE_URL = os.getenv(
    "DATABASE_URL_TEST",
    "sqlite+aiosqlite:///:memory:"
)

# Determine database type
IS_MYSQL = "mysql" in TEST_DATABASE_URL
IS_SQLITE = "sqlite" in TEST_DATABASE_URL

# Connection pool settings from environment (with defaults)
TEST_DB_POOL_SIZE = int(os.getenv("TEST_DB_POOL_SIZE", "5"))
TEST_DB_MAX_OVERFLOW = int(os.getenv("TEST_DB_MAX_OVERFLOW", "5"))
TEST_DB_POOL_RECYCLE = int(os.getenv("TEST_DB_POOL_RECYCLE", "1800"))
TEST_DB_POOL_PRE_PING = os.getenv("TEST_DB_POOL_PRE_PING", "true").lower() == "true"
TEST_DB_ECHO = os.getenv("TEST_DB_ECHO_SQL", "false").lower() == "true"


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
        # SQLite configuration: Use StaticPool for :memory: database
        # This ensures single connection shared across all tests
        return {
            "url": TEST_DATABASE_URL,
            "echo": TEST_DB_ECHO,
            "poolclass": StaticPool,
            "connect_args": {
                "check_same_thread": False,  # Allow multi-threaded access
            }
        }
    elif IS_MYSQL:
        # MySQL configuration: Use QueuePool for connection pooling
        return {
            "url": TEST_DATABASE_URL,
            "echo": TEST_DB_ECHO,
            "poolclass": QueuePool,
            "pool_size": TEST_DB_POOL_SIZE,
            "max_overflow": TEST_DB_MAX_OVERFLOW,
            "pool_recycle": TEST_DB_POOL_RECYCLE,
            "pool_pre_ping": TEST_DB_POOL_PRE_PING,
            "pool_timeout": 30,
            # MySQL specific settings
            "connect_args": {
                "charset": "utf8mb4",
                "autocommit": False,
            },
            # Enable better async performance
            "execution_options": {
                "isolation_level": "READ COMMITTED"
            }
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

    Configuration:
    - expire_on_commit=False: Keep objects accessible after commit
    - autocommit=False: Manual transaction control
    - autoflush=False: Manual flush control for predictable behavior

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


# Pytest markers for conditional test execution
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "mysql: mark test to run only with MySQL database"
    )
    config.addinivalue_line(
        "markers", "sqlite: mark test to run only with SQLite database"
    )


def pytest_collection_modifyitems(config, items):
    """
    Modify test collection based on database type.

    Skip tests marked for specific databases when using other databases.
    """
    for item in items:
        if "mysql" in item.keywords and IS_SQLITE:
            item.add_marker(pytest.mark.skip(reason="MySQL-only test, running with SQLite"))
        if "sqlite" in item.keywords and IS_MYSQL:
            item.add_marker(pytest.mark.skip(reason="SQLite-only test, running with MySQL"))


# Display test configuration on startup
def pytest_report_header(config):
    """Display test database configuration in pytest header."""
    return [
        f"Test Database: {'MySQL' if IS_MYSQL else 'SQLite'}",
        f"Database URL: {TEST_DATABASE_URL}",
        f"Pool Size: {TEST_DB_POOL_SIZE if IS_MYSQL else 'N/A (StaticPool)'}",
        f"Echo SQL: {TEST_DB_ECHO}",
    ]
