"""
Import Task Repository Tests

TDD tests for ImportTaskRepository functionality.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.import_task import ImportTask, ImportStatus, ImportType
from app.database.repositories.import_task import ImportTaskRepository


class TestImportTaskRepository:
    """Test suite for ImportTaskRepository"""

    @pytest.mark.asyncio
    async def test_create_import_task(
        self,
        import_task_repo: ImportTaskRepository,
        db_session: AsyncSession
    ):
        """Test creating an import task"""
        # Arrange
        task_data = {
            "task_name": "New Import",
            "import_type": ImportType.CSV.value,
            "status": ImportStatus.PENDING.value,
            "original_filename": "data.csv",
            "file_path": "/tmp/data.csv",
            "file_size": 2048,
            "user_id": "user_456"
        }

        # Act
        task = await import_task_repo.create(obj_in=task_data, commit=True)

        # Assert
        assert task.id is not None
        assert task.task_name == "New Import"
        assert task.status == ImportStatus.PENDING.value
        assert task.file_size == 2048
        assert task.progress_percentage == 0.0

        # Cleanup
        await import_task_repo.delete(task.id, soft=False, commit=True)

    @pytest.mark.asyncio
    async def test_get_by_user(
        self,
        import_task_repo: ImportTaskRepository,
        sample_import_task: ImportTask
    ):
        """Test getting import tasks by user ID"""
        # Act
        tasks = await import_task_repo.get_by_user("test_user_123")

        # Assert
        assert len(tasks) >= 1
        assert any(t.id == sample_import_task.id for t in tasks)
        assert all(t.user_id == "test_user_123" for t in tasks)

    @pytest.mark.asyncio
    async def test_get_by_status(
        self,
        import_task_repo: ImportTaskRepository,
        sample_import_task: ImportTask
    ):
        """Test getting import tasks by status"""
        # Act
        pending_tasks = await import_task_repo.get_by_status(ImportStatus.PENDING)

        # Assert
        assert len(pending_tasks) >= 1
        assert any(t.id == sample_import_task.id for t in pending_tasks)
        assert all(t.status == ImportStatus.PENDING.value for t in pending_tasks)

    @pytest.mark.asyncio
    async def test_get_active_tasks(
        self,
        import_task_repo: ImportTaskRepository,
        sample_import_task: ImportTask
    ):
        """Test getting active import tasks"""
        # Act
        active_tasks = await import_task_repo.get_active_tasks()

        # Assert
        assert len(active_tasks) >= 1
        assert any(t.id == sample_import_task.id for t in active_tasks)

    @pytest.mark.asyncio
    async def test_update_progress(
        self,
        import_task_repo: ImportTaskRepository,
        sample_import_task: ImportTask,
        db_session: AsyncSession
    ):
        """Test updating import task progress"""
        # Arrange
        task = sample_import_task

        # Act
        task.update_progress(processed=500, total=1000)
        await db_session.commit()
        await db_session.refresh(task)

        # Assert
        assert task.processed_rows == 500
        assert task.total_rows == 1000
        assert task.progress_percentage == 50.0

    @pytest.mark.asyncio
    async def test_count_by_status(
        self,
        import_task_repo: ImportTaskRepository,
        sample_import_task: ImportTask
    ):
        """Test counting import tasks by status"""
        # Act
        count = await import_task_repo.count_by_status(ImportStatus.PENDING)

        # Assert
        assert count >= 1

    @pytest.mark.asyncio
    async def test_soft_delete_import_task(
        self,
        import_task_repo: ImportTaskRepository,
        db_session: AsyncSession
    ):
        """Test soft deleting an import task"""
        # Arrange
        task_data = {
            "task_name": "To Delete",
            "import_type": ImportType.EXCEL.value,
            "status": ImportStatus.COMPLETED.value,
            "original_filename": "delete_me.xlsx",
            "file_path": "/tmp/delete_me.xlsx",
            "file_size": 512
        }
        task = await import_task_repo.create(obj_in=task_data, commit=True)
        task_id = task.id

        # Act
        deleted = await import_task_repo.delete(task_id, soft=True, commit=True)

        # Assert
        assert deleted is True
        deleted_task = await import_task_repo.get(task_id)
        assert deleted_task.is_deleted is True

        # Cleanup
        await import_task_repo.delete(task_id, soft=False, commit=True)

    @pytest.mark.asyncio
    async def test_filter_by_import_type(
        self,
        import_task_repo: ImportTaskRepository,
        sample_import_task: ImportTask
    ):
        """Test filtering tasks by import type"""
        # Act
        csv_tasks = await import_task_repo.get_by_user(
            "test_user_123"
        )

        # Assert
        assert len(csv_tasks) >= 1
        assert sample_import_task.id in [t.id for t in csv_tasks]
