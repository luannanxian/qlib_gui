"""
Pytest Configuration for Data Preprocessing Tests

Provides fixtures for testing preprocessing functionality.
"""

import asyncio
from typing import AsyncGenerator

import pandas as pd
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.database.base import Base
# Import all models to register them with Base.metadata
from app.database.models.dataset import Dataset
from app.database.models.chart import ChartConfig
from app.database.models.user_preferences import UserPreferences
from app.database.models.import_task import ImportTask
from app.database.models.preprocessing import (
    DataPreprocessingRule, DataPreprocessingTask
)
from app.database.repositories.preprocessing import (
    PreprocessingRuleRepository, PreprocessingTaskRepository
)

# Test database URL (use file-based SQLite for testing to avoid connection issues)
import tempfile
import os
TEST_DB_FILE = os.path.join(tempfile.gettempdir(), "test_preprocessing.db")
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
    # Remove old test database if it exists
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

    # Clean up test database file
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
async def rule_repo(db_session: AsyncSession) -> PreprocessingRuleRepository:
    """Create a PreprocessingRuleRepository instance for testing"""
    return PreprocessingRuleRepository(db_session)


@pytest_asyncio.fixture
async def task_repo(db_session: AsyncSession) -> PreprocessingTaskRepository:
    """Create a PreprocessingTaskRepository instance for testing"""
    return PreprocessingTaskRepository(db_session)


@pytest.fixture
def sample_dataframe() -> pd.DataFrame:
    """Create a sample DataFrame for testing preprocessing operations"""
    return pd.DataFrame({
        'price': [100, 200, 300, None, 500, 1000, 150],
        'volume': [1000, 2000, 3000, 4000, None, 6000, 1500],
        'symbol': ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'NVDA', 'META'],
        'date': pd.date_range('2024-01-01', periods=7)
    })


@pytest.fixture
def sample_dataframe_with_outliers() -> pd.DataFrame:
    """Create a DataFrame with outliers for testing outlier detection"""
    return pd.DataFrame({
        'price': [100, 110, 105, 108, 112, 5000, 109],  # 5000 is outlier
        'volume': [1000, 1100, 1050, 1080, 50, 1200, 1090],  # 50 is outlier
        'symbol': ['A', 'B', 'C', 'D', 'E', 'F', 'G']
    })


@pytest.fixture
def sample_dataframe_empty() -> pd.DataFrame:
    """Create an empty DataFrame for edge case testing"""
    return pd.DataFrame()


@pytest.fixture
def sample_dataframe_all_missing() -> pd.DataFrame:
    """Create a DataFrame with all missing values for edge case testing"""
    return pd.DataFrame({
        'price': [None, None, None],
        'volume': [None, None, None]
    })
