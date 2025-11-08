"""
TDD Tests for Task Repository

Test coverage for:
- Task CRUD operations
- Query by status, type, priority
- Query by user
- Pagination
- Status updates
- Error handling
"""

import pytest
from datetime import datetime
from decimal import Decimal

from app.database.models.task import Task, TaskType, TaskStatus, TaskPriority
from app.database.repositories.task_repository import TaskRepository


class TestTaskRepository:
    """Test TaskRepository CRUD operations."""

    @pytest.fixture
    async def repository(self, db_session):
        """Create a TaskRepository instance for testing."""
        return TaskRepository(db_session)

    @pytest.fixture
    async def sample_task_data(self):
        """Sample task data for testing."""
        return {
            "type": TaskType.BACKTEST.value,
            "name": "Test Backtest Task",
            "status": TaskStatus.PENDING.value,
            "priority": TaskPriority.NORMAL.value,
            "params": {"strategy_id": "test_strategy", "dataset_id": "test_dataset"},
            "progress": 0.0,
            "created_by": "test_user"
        }

    @pytest.mark.asyncio
    async def test_create_task(self, repository: TaskRepository, sample_task_data):
        """Test creating a new task."""
        # ACT
        task = await repository.create_task(sample_task_data)

        # ASSERT
        assert task.id is not None
        assert task.type == TaskType.BACKTEST.value
        assert task.name == "Test Backtest Task"
        assert task.status == TaskStatus.PENDING.value
        assert task.priority == TaskPriority.NORMAL.value
        assert task.progress == 0.0
        assert task.created_by == "test_user"
        assert task.created_at is not None

    @pytest.mark.asyncio
    async def test_get_task_by_id(self, repository: TaskRepository, sample_task_data):
        """Test retrieving a task by ID."""
        # ARRANGE
        created_task = await repository.create_task(sample_task_data)

        # ACT
        task = await repository.get_task_by_id(created_task.id)

        # ASSERT
        assert task is not None
        assert task.id == created_task.id
        assert task.name == "Test Backtest Task"

    @pytest.mark.asyncio
    async def test_get_task_by_id_not_found(self, repository: TaskRepository):
        """Test retrieving a non-existent task returns None."""
        # ACT
        task = await repository.get_task_by_id("non_existent_id")

        # ASSERT
        assert task is None

    @pytest.mark.asyncio
    async def test_get_tasks_by_status(self, repository: TaskRepository, sample_task_data):
        """Test retrieving tasks by status."""
        # ARRANGE
        await repository.create_task(sample_task_data)
        await repository.create_task({**sample_task_data, "name": "Task 2"})

        running_data = {**sample_task_data, "name": "Running Task", "status": TaskStatus.RUNNING.value}
        await repository.create_task(running_data)

        # ACT
        pending_tasks = await repository.get_tasks_by_status(TaskStatus.PENDING.value)
        running_tasks = await repository.get_tasks_by_status(TaskStatus.RUNNING.value)

        # ASSERT
        assert len(pending_tasks) == 2
        assert len(running_tasks) == 1
        assert all(t.status == TaskStatus.PENDING.value for t in pending_tasks)
        assert running_tasks[0].status == TaskStatus.RUNNING.value

    @pytest.mark.asyncio
    async def test_get_tasks_by_type(self, repository: TaskRepository, sample_task_data):
        """Test retrieving tasks by type."""
        # ARRANGE
        await repository.create_task(sample_task_data)

        import_data = {
            **sample_task_data,
            "name": "Import Task",
            "type": TaskType.DATA_IMPORT.value
        }
        await repository.create_task(import_data)

        # ACT
        backtest_tasks = await repository.get_tasks_by_type(TaskType.BACKTEST.value)
        import_tasks = await repository.get_tasks_by_type(TaskType.DATA_IMPORT.value)

        # ASSERT
        assert len(backtest_tasks) == 1
        assert len(import_tasks) == 1
        assert backtest_tasks[0].type == TaskType.BACKTEST.value
        assert import_tasks[0].type == TaskType.DATA_IMPORT.value

    @pytest.mark.asyncio
    async def test_get_tasks_by_user(self, repository: TaskRepository, sample_task_data):
        """Test retrieving tasks by user."""
        # ARRANGE
        await repository.create_task(sample_task_data)
        await repository.create_task({**sample_task_data, "name": "Task 2"})

        other_user_data = {**sample_task_data, "name": "Other User Task", "created_by": "other_user"}
        await repository.create_task(other_user_data)

        # ACT
        test_user_tasks = await repository.get_tasks_by_user("test_user")
        other_user_tasks = await repository.get_tasks_by_user("other_user")

        # ASSERT
        assert len(test_user_tasks) == 2
        assert len(other_user_tasks) == 1
        assert all(t.created_by == "test_user" for t in test_user_tasks)
        assert other_user_tasks[0].created_by == "other_user"

    @pytest.mark.asyncio
    async def test_get_tasks_with_pagination(self, repository: TaskRepository, sample_task_data):
        """Test retrieving tasks with pagination."""
        # ARRANGE
        for i in range(5):
            await repository.create_task({**sample_task_data, "name": f"Task {i}"})

        # ACT
        page1 = await repository.get_tasks(skip=0, limit=2)
        page2 = await repository.get_tasks(skip=2, limit=2)
        page3 = await repository.get_tasks(skip=4, limit=2)

        # ASSERT
        assert len(page1) == 2
        assert len(page2) == 2
        assert len(page3) == 1

    @pytest.mark.asyncio
    async def test_update_task_status(self, repository: TaskRepository, sample_task_data):
        """Test updating task status."""
        # ARRANGE
        task = await repository.create_task(sample_task_data)

        # ACT
        updated_task = await repository.update_task_status(task.id, TaskStatus.RUNNING.value)

        # ASSERT
        assert updated_task is not None
        assert updated_task.status == TaskStatus.RUNNING.value

    @pytest.mark.asyncio
    async def test_update_task_progress(self, repository: TaskRepository, sample_task_data):
        """Test updating task progress."""
        # ARRANGE
        task = await repository.create_task(sample_task_data)

        # ACT
        updated_task = await repository.update_task(
            task.id,
            {
                "progress": 50.0,
                "current_step": "Processing data",
                "eta": 120
            }
        )

        # ASSERT
        assert updated_task is not None
        assert updated_task.progress == 50.0
        assert updated_task.current_step == "Processing data"
        assert updated_task.eta == 120

    @pytest.mark.asyncio
    async def test_update_task_result(self, repository: TaskRepository, sample_task_data):
        """Test updating task with result."""
        # ARRANGE
        task = await repository.create_task(sample_task_data)

        # ACT
        result_data = {
            "total_return": 0.15,
            "sharpe_ratio": 1.5,
            "max_drawdown": -0.08
        }
        updated_task = await repository.update_task(
            task.id,
            {
                "status": TaskStatus.COMPLETED.value,
                "progress": 100.0,
                "result": result_data
            }
        )

        # ASSERT
        assert updated_task is not None
        assert updated_task.status == TaskStatus.COMPLETED.value
        assert updated_task.progress == 100.0
        assert updated_task.result == result_data

    @pytest.mark.asyncio
    async def test_update_task_with_error(self, repository: TaskRepository, sample_task_data):
        """Test updating task with error."""
        # ARRANGE
        task = await repository.create_task(sample_task_data)

        # ACT
        updated_task = await repository.update_task(
            task.id,
            {
                "status": TaskStatus.FAILED.value,
                "error": "Database connection timeout"
            }
        )

        # ASSERT
        assert updated_task is not None
        assert updated_task.status == TaskStatus.FAILED.value
        assert updated_task.error == "Database connection timeout"

    @pytest.mark.asyncio
    async def test_delete_task(self, repository: TaskRepository, sample_task_data):
        """Test soft deleting a task."""
        # ARRANGE
        task = await repository.create_task(sample_task_data)

        # ACT
        result = await repository.delete_task(task.id)

        # ASSERT
        assert result is True
        deleted_task = await repository.get_task_by_id(task.id)
        assert deleted_task is None

    @pytest.mark.asyncio
    async def test_delete_task_not_found(self, repository: TaskRepository):
        """Test deleting a non-existent task returns False."""
        # ACT
        result = await repository.delete_task("non_existent_id")

        # ASSERT
        assert result is False

    @pytest.mark.asyncio
    async def test_get_pending_tasks_by_priority(self, repository: TaskRepository, sample_task_data):
        """Test retrieving pending tasks ordered by priority."""
        # ARRANGE
        await repository.create_task({**sample_task_data, "priority": TaskPriority.LOW.value})
        await repository.create_task({**sample_task_data, "priority": TaskPriority.URGENT.value})
        await repository.create_task({**sample_task_data, "priority": TaskPriority.HIGH.value})
        await repository.create_task({**sample_task_data, "priority": TaskPriority.NORMAL.value})

        # ACT
        tasks = await repository.get_pending_tasks_by_priority()

        # ASSERT
        assert len(tasks) == 4
        # Should be ordered by priority descending (URGENT -> HIGH -> NORMAL -> LOW)
        assert tasks[0].priority == TaskPriority.URGENT.value
        assert tasks[1].priority == TaskPriority.HIGH.value
        assert tasks[2].priority == TaskPriority.NORMAL.value
        assert tasks[3].priority == TaskPriority.LOW.value

    @pytest.mark.asyncio
    async def test_count_tasks_by_status(self, repository: TaskRepository, sample_task_data):
        """Test counting tasks by status."""
        # ARRANGE
        await repository.create_task(sample_task_data)
        await repository.create_task({**sample_task_data, "name": "Task 2"})
        await repository.create_task({
            **sample_task_data,
            "name": "Running Task",
            "status": TaskStatus.RUNNING.value
        })

        # ACT
        pending_count = await repository.count_tasks_by_status(TaskStatus.PENDING.value)
        running_count = await repository.count_tasks_by_status(TaskStatus.RUNNING.value)
        completed_count = await repository.count_tasks_by_status(TaskStatus.COMPLETED.value)

        # ASSERT
        assert pending_count == 2
        assert running_count == 1
        assert completed_count == 0

    @pytest.mark.asyncio
    async def test_get_running_tasks(self, repository: TaskRepository, sample_task_data):
        """Test retrieving all running tasks."""
        # ARRANGE
        await repository.create_task(sample_task_data)
        await repository.create_task({
            **sample_task_data,
            "name": "Running Task 1",
            "status": TaskStatus.RUNNING.value
        })
        await repository.create_task({
            **sample_task_data,
            "name": "Running Task 2",
            "status": TaskStatus.RUNNING.value
        })

        # ACT
        running_tasks = await repository.get_running_tasks()

        # ASSERT
        assert len(running_tasks) == 2
        assert all(t.status == TaskStatus.RUNNING.value for t in running_tasks)

    @pytest.mark.asyncio
    async def test_update_task_not_found(self, repository: TaskRepository):
        """Test updating a non-existent task returns None."""
        # ACT
        result = await repository.update_task("non_existent_id", {"progress": 50.0})

        # ASSERT
        assert result is None
