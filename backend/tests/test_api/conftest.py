"""
Pytest Configuration for Preprocessing API Tests

Imports shared fixtures from the API tests conftest.
This allows tests to use the 'client' fixture.
"""

import sys
from pathlib import Path

# Add parent directory to path to import conftest from modules/data_management/api
parent_conftest_dir = Path(__file__).parent.parent / "modules" / "data_management" / "api"
sys.path.insert(0, str(parent_conftest_dir))

# Import all fixtures from the parent conftest
# This makes the 'client' fixture available to tests in this directory
pytest_plugins = ["tests.modules.data_management.api.conftest"]

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.preprocessing import (
    PreprocessingRuleRepository,
    PreprocessingTaskRepository
)


@pytest_asyncio.fixture
async def rule_repo(db_session: AsyncSession) -> PreprocessingRuleRepository:
    """Create a PreprocessingRuleRepository instance for testing"""
    return PreprocessingRuleRepository(db_session)


@pytest_asyncio.fixture
async def task_repo(db_session: AsyncSession) -> PreprocessingTaskRepository:
    """Create a PreprocessingTaskRepository instance for testing"""
    return PreprocessingTaskRepository(db_session)

