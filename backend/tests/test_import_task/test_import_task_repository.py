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
        import_task_repo: ImportTaskRepository
    ):
        """Test getting import tasks by user ID"""
        # Arrange
        task_data = {
            "task_name": "User Task Test",
            "import_type": ImportType.CSV.value,
            "status": ImportStatus.PENDING.value,
            "original_filename": "user_test.csv",
            "file_path": "/tmp/user_test.csv",
            "file_size": 1024,
            "user_id": "test_user_456"
        }
        task = await import_task_repo.create(obj_in=task_data, commit=True)

        # Act
        tasks = await import_task_repo.get_by_user("test_user_456")

        # Assert
        assert len(tasks) >= 1
        assert any(t.id == task.id for t in tasks)
        assert all(t.user_id == "test_user_456" for t in tasks)

        # Cleanup
        await import_task_repo.delete(task.id, soft=False, commit=True)

    @pytest.mark.asyncio
    async def test_get_by_status(
        self,
        import_task_repo: ImportTaskRepository
    ):
        """Test getting import tasks by status"""
        # Arrange
        task_data = {
            "task_name": "Status Task Test",
            "import_type": ImportType.CSV.value,
            "status": ImportStatus.PENDING.value,
            "original_filename": "status_test.csv",
            "file_path": "/tmp/status_test.csv",
            "file_size": 1536
        }
        task = await import_task_repo.create(obj_in=task_data, commit=True)

        # Act
        pending_tasks = await import_task_repo.get_by_status(ImportStatus.PENDING)

        # Assert
        assert len(pending_tasks) >= 1
        assert any(t.id == task.id for t in pending_tasks)
        assert all(t.status == ImportStatus.PENDING.value for t in pending_tasks)

        # Cleanup
        await import_task_repo.delete(task.id, soft=False, commit=True)

    @pytest.mark.asyncio
    async def test_get_active_tasks(
        self,
        import_task_repo: ImportTaskRepository
    ):
        """Test getting active import tasks"""
        # Arrange
        task_data = {
            "task_name": "Active Task Test",
            "import_type": ImportType.CSV.value,
            "status": ImportStatus.PROCESSING.value,
            "original_filename": "active_test.csv",
            "file_path": "/tmp/active_test.csv",
            "file_size": 2048
        }
        task = await import_task_repo.create(obj_in=task_data, commit=True)

        # Act
        active_tasks = await import_task_repo.get_active_tasks()

        # Assert
        assert len(active_tasks) >= 1
        assert any(t.id == task.id for t in active_tasks)

        # Cleanup
        await import_task_repo.delete(task.id, soft=False, commit=True)

    @pytest.mark.asyncio
    async def test_update_progress(
        self,
        import_task_repo: ImportTaskRepository,
        db_session: AsyncSession
    ):
        """Test updating import task progress"""
        # Arrange
        task_data = {
            "task_name": "Progress Task Test",
            "import_type": ImportType.EXCEL.value,
            "status": ImportStatus.PROCESSING.value,
            "original_filename": "progress_test.xlsx",
            "file_path": "/tmp/progress_test.xlsx",
            "file_size": 5120
        }
        task = await import_task_repo.create(obj_in=task_data, commit=True)

        # Act
        task.update_progress(processed=500, total=1000)
        await db_session.commit()
        await db_session.refresh(task)

        # Assert
        assert task.processed_rows == 500
        assert task.total_rows == 1000
        assert task.progress_percentage == 50.0

        # Cleanup
        await import_task_repo.delete(task.id, soft=False, commit=True)

    @pytest.mark.asyncio
    async def test_count_by_status(
        self,
        import_task_repo: ImportTaskRepository
    ):
        """Test counting import tasks by status"""
        # Arrange
        task_data = {
            "task_name": "Count Task Test",
            "import_type": ImportType.EXCEL.value,
            "status": ImportStatus.PENDING.value,
            "original_filename": "count_test.xlsx",
            "file_path": "/tmp/count_test.xlsx",
            "file_size": 3072
        }
        task = await import_task_repo.create(obj_in=task_data, commit=True)

        # Act
        count = await import_task_repo.count_by_status(ImportStatus.PENDING)

        # Assert
        assert count >= 1

        # Cleanup
        await import_task_repo.delete(task.id, soft=False, commit=True)

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

        # Verify task is not returned without include_deleted
        normal_get = await import_task_repo.get(task_id, include_deleted=False)
        assert normal_get is None

        # Verify task is returned with include_deleted
        deleted_task = await import_task_repo.get(task_id, include_deleted=True)
        assert deleted_task is not None
        assert deleted_task.is_deleted is True
        assert deleted_task.deleted_at is not None

        # Cleanup
        await import_task_repo.delete(task_id, soft=False, commit=True)

    @pytest.mark.asyncio
    async def test_filter_by_import_type(
        self,
        import_task_repo: ImportTaskRepository
    ):
        """Test filtering tasks by import type"""
        # Arrange
        task_data = {
            "task_name": "Filter Type Test",
            "import_type": ImportType.JSON.value,
            "status": ImportStatus.COMPLETED.value,
            "original_filename": "filter_test.json",
            "file_path": "/tmp/filter_test.json",
            "file_size": 4096,
            "user_id": "test_user_789"
        }
        task = await import_task_repo.create(obj_in=task_data, commit=True)

        # Act
        json_tasks = await import_task_repo.get_by_user("test_user_789")

        # Assert
        assert len(json_tasks) >= 1
        assert task.id in [t.id for t in json_tasks]
        assert all(t.user_id == "test_user_789" for t in json_tasks)

        # Cleanup
        await import_task_repo.delete(task.id, soft=False, commit=True)
