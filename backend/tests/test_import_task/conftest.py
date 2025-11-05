"""
Pytest Configuration for Import Task Tests

Provides fixtures for testing import task functionality.
"""

import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import db_manager
from app.database.models.import_task import ImportTask
from app.database.repositories.import_task import ImportTaskRepository


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def init_database():
    """Initialize database for tests"""
    db_manager.init()
    yield
    await db_manager.close()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide database session for tests"""
    async with db_manager.session() as session:
        yield session


@pytest.fixture
async def import_task_repo(db_session: AsyncSession) -> ImportTaskRepository:
    """Provide import task repository"""
    return ImportTaskRepository(db_session)


@pytest.fixture
async def sample_import_task(db_session: AsyncSession) -> ImportTask:
    """Create sample import task for testing"""
    from app.database.models.import_task import ImportStatus, ImportType

    task = ImportTask(
        task_name="Test Import Task",
        import_type=ImportType.CSV.value,
        status=ImportStatus.PENDING.value,
        original_filename="test_data.csv",
        file_path="/tmp/test_data.csv",
        file_size=1024,
        user_id="test_user_123"
    )

    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    yield task

    # Cleanup
    await db_session.delete(task)
    await db_session.commit()
