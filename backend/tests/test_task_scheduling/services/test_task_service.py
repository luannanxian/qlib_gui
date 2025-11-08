"""
TDD Tests for Task Service

Test coverage for:
- Task creation and validation
- Task lifecycle management (start, pause, resume, cancel, complete)
- Task queue management
- Task status transitions
- Error handling and recovery
- Task priority management
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

from app.database.models.task import Task, TaskType, TaskStatus, TaskPriority
from app.modules.task_scheduling.services.task_service import TaskService
from app.modules.task_scheduling.exceptions import (
    TaskNotFoundError,
    TaskValidationError,
    TaskExecutionError
)


class TestTaskService:
    """Test TaskService business logic."""

    @pytest.fixture
    def mock_repository(self, mocker):
        """Create a mock TaskRepository."""
        return mocker.Mock()

    @pytest.fixture
    def service(self, mock_repository):
        """Create a TaskService instance with mocked repository."""
        return TaskService(mock_repository)

    @pytest.fixture
    def sample_task_data(self):
        """Sample task data for testing."""
        return {
            "type": TaskType.BACKTEST.value,
            "name": "Test Backtest Task",
            "params": {"strategy_id": "test_strategy", "dataset_id": "test_dataset"},
            "created_by": "test_user"
        }

    # ==================== Task Creation Tests ====================

    @pytest.mark.asyncio
    async def test_create_task_success(self, service: TaskService, mock_repository, sample_task_data):
        """Test successful task creation."""
        # ARRANGE
        expected_task = Task(
            id="task_123",
            status=TaskStatus.PENDING.value,
            priority=TaskPriority.NORMAL.value,
            progress=0.0,
            **sample_task_data
        )
        mock_repository.create_task = AsyncMock(return_value=expected_task)

        # ACT
        task = await service.create_task(sample_task_data)

        # ASSERT
        assert task.id == "task_123"
        assert task.status == TaskStatus.PENDING.value
        assert task.priority == TaskPriority.NORMAL.value
        mock_repository.create_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_task_with_priority(self, service: TaskService, mock_repository, sample_task_data):
        """Test creating task with custom priority."""
        # ARRANGE
        task_data = {**sample_task_data, "priority": TaskPriority.HIGH.value}
        expected_task = Task(id="task_123", status=TaskStatus.PENDING.value, **task_data)
        mock_repository.create_task = AsyncMock(return_value=expected_task)

        # ACT
        task = await service.create_task(task_data)

        # ASSERT
        assert task.priority == TaskPriority.HIGH.value

    @pytest.mark.asyncio
    async def test_create_task_validation_error(self, service: TaskService, sample_task_data):
        """Test task creation with invalid data."""
        # ARRANGE
        invalid_data = {**sample_task_data}
        del invalid_data["type"]  # Missing required field

        # ACT & ASSERT
        with pytest.raises(TaskValidationError):
            await service.create_task(invalid_data)

    # ==================== Task Retrieval Tests ====================

    @pytest.mark.asyncio
    async def test_get_task_by_id_success(self, service: TaskService, mock_repository):
        """Test retrieving task by ID."""
        # ARRANGE
        expected_task = Task(
            id="task_123",
            type=TaskType.BACKTEST.value,
            name="Test Task",
            status=TaskStatus.PENDING.value,
            params={},
            created_by="test_user"
        )
        mock_repository.get_task_by_id = AsyncMock(return_value=expected_task)

        # ACT
        task = await service.get_task("task_123")

        # ASSERT
        assert task.id == "task_123"
        mock_repository.get_task_by_id.assert_called_once_with("task_123")

    @pytest.mark.asyncio
    async def test_get_task_not_found(self, service: TaskService, mock_repository):
        """Test retrieving non-existent task."""
        # ARRANGE
        mock_repository.get_task_by_id = AsyncMock(return_value=None)

        # ACT & ASSERT
        with pytest.raises(TaskNotFoundError):
            await service.get_task("non_existent_id")

    @pytest.mark.asyncio
    async def test_list_tasks_with_filters(self, service: TaskService, mock_repository):
        """Test listing tasks with filters."""
        # ARRANGE
        tasks = [
            Task(id=f"task_{i}", type=TaskType.BACKTEST.value, name=f"Task {i}",
                 status=TaskStatus.PENDING.value, params={}, created_by="test_user")
            for i in range(3)
        ]
        mock_repository.get_tasks = AsyncMock(return_value=tasks)

        # ACT
        result = await service.list_tasks(skip=0, limit=10)

        # ASSERT
        assert len(result) == 3
        mock_repository.get_tasks.assert_called_once_with(skip=0, limit=10)

    # ==================== Task Lifecycle Tests ====================

    @pytest.mark.asyncio
    async def test_start_task_success(self, service: TaskService, mock_repository):
        """Test starting a pending task."""
        # ARRANGE
        task = Task(
            id="task_123",
            type=TaskType.BACKTEST.value,
            name="Test Task",
            status=TaskStatus.PENDING.value,
            params={},
            created_by="test_user"
        )
        mock_repository.get_task_by_id = AsyncMock(return_value=task)
        mock_repository.update_task_status = AsyncMock(return_value=task)

        # ACT
        result = await service.start_task("task_123")

        # ASSERT
        assert result.status == TaskStatus.RUNNING.value
        mock_repository.update_task_status.assert_called_once_with("task_123", TaskStatus.RUNNING.value)

    @pytest.mark.asyncio
    async def test_start_task_invalid_status(self, service: TaskService, mock_repository):
        """Test starting task with invalid status."""
        # ARRANGE
        task = Task(
            id="task_123",
            type=TaskType.BACKTEST.value,
            name="Test Task",
            status=TaskStatus.COMPLETED.value,  # Already completed
            params={},
            created_by="test_user"
        )
        mock_repository.get_task_by_id = AsyncMock(return_value=task)

        # ACT & ASSERT
        with pytest.raises(TaskExecutionError, match="Cannot start task with status"):
            await service.start_task("task_123")

    @pytest.mark.asyncio
    async def test_pause_task_success(self, service: TaskService, mock_repository):
        """Test pausing a running task."""
        # ARRANGE
        task = Task(
            id="task_123",
            type=TaskType.BACKTEST.value,
            name="Test Task",
            status=TaskStatus.RUNNING.value,
            params={},
            created_by="test_user"
        )
        mock_repository.get_task_by_id = AsyncMock(return_value=task)
        mock_repository.update_task_status = AsyncMock(return_value=task)

        # ACT
        result = await service.pause_task("task_123")

        # ASSERT
        assert result.status == TaskStatus.PAUSED.value
        mock_repository.update_task_status.assert_called_once_with("task_123", TaskStatus.PAUSED.value)

    @pytest.mark.asyncio
    async def test_resume_task_success(self, service: TaskService, mock_repository):
        """Test resuming a paused task."""
        # ARRANGE
        task = Task(
            id="task_123",
            type=TaskType.BACKTEST.value,
            name="Test Task",
            status=TaskStatus.PAUSED.value,
            params={},
            created_by="test_user"
        )
        mock_repository.get_task_by_id = AsyncMock(return_value=task)
        mock_repository.update_task_status = AsyncMock(return_value=task)

        # ACT
        result = await service.resume_task("task_123")

        # ASSERT
        assert result.status == TaskStatus.RUNNING.value
        mock_repository.update_task_status.assert_called_once_with("task_123", TaskStatus.RUNNING.value)

    @pytest.mark.asyncio
    async def test_cancel_task_success(self, service: TaskService, mock_repository):
        """Test cancelling a task."""
        # ARRANGE
        task = Task(
            id="task_123",
            type=TaskType.BACKTEST.value,
            name="Test Task",
            status=TaskStatus.RUNNING.value,
            params={},
            created_by="test_user"
        )
        mock_repository.get_task_by_id = AsyncMock(return_value=task)
        mock_repository.update_task_status = AsyncMock(return_value=task)

        # ACT
        result = await service.cancel_task("task_123")

        # ASSERT
        assert result.status == TaskStatus.CANCELLED.value
        mock_repository.update_task_status.assert_called_once_with("task_123", TaskStatus.CANCELLED.value)

    @pytest.mark.asyncio
    async def test_complete_task_success(self, service: TaskService, mock_repository):
        """Test completing a task with result."""
        # ARRANGE
        task = Task(
            id="task_123",
            type=TaskType.BACKTEST.value,
            name="Test Task",
            status=TaskStatus.RUNNING.value,
            params={},
            created_by="test_user"
        )
        result_data = {"total_return": 0.15, "sharpe_ratio": 1.5}
        mock_repository.get_task_by_id = AsyncMock(return_value=task)
        mock_repository.update_task = AsyncMock(return_value=task)

        # ACT
        result = await service.complete_task("task_123", result_data)

        # ASSERT
        assert result.status == TaskStatus.COMPLETED.value
        mock_repository.update_task.assert_called_once()
        call_args = mock_repository.update_task.call_args[0]
        assert call_args[0] == "task_123"
        assert call_args[1]["status"] == TaskStatus.COMPLETED.value
        assert call_args[1]["result"] == result_data
        assert call_args[1]["progress"] == 100.0

    @pytest.mark.asyncio
    async def test_fail_task_with_error(self, service: TaskService, mock_repository):
        """Test marking task as failed with error message."""
        # ARRANGE
        task = Task(
            id="task_123",
            type=TaskType.BACKTEST.value,
            name="Test Task",
            status=TaskStatus.RUNNING.value,
            params={},
            created_by="test_user"
        )
        error_message = "Database connection timeout"
        mock_repository.get_task_by_id = AsyncMock(return_value=task)
        mock_repository.update_task = AsyncMock(return_value=task)

        # ACT
        result = await service.fail_task("task_123", error_message)

        # ASSERT
        assert result.status == TaskStatus.FAILED.value
        mock_repository.update_task.assert_called_once()
        call_args = mock_repository.update_task.call_args[0]
        assert call_args[1]["status"] == TaskStatus.FAILED.value
        assert call_args[1]["error"] == error_message

    # ==================== Task Progress Tests ====================

    @pytest.mark.asyncio
    async def test_update_task_progress(self, service: TaskService, mock_repository):
        """Test updating task progress."""
        # ARRANGE
        task = Task(
            id="task_123",
            type=TaskType.BACKTEST.value,
            name="Test Task",
            status=TaskStatus.RUNNING.value,
            params={},
            created_by="test_user"
        )
        mock_repository.get_task_by_id = AsyncMock(return_value=task)
        mock_repository.update_task = AsyncMock(return_value=task)

        # ACT
        result = await service.update_progress(
            "task_123",
            progress=50.0,
            current_step="Processing data",
            eta=120
        )

        # ASSERT
        mock_repository.update_task.assert_called_once()
        call_args = mock_repository.update_task.call_args[0]
        assert call_args[1]["progress"] == 50.0
        assert call_args[1]["current_step"] == "Processing data"
        assert call_args[1]["eta"] == 120

    # ==================== Task Queue Management Tests ====================

    @pytest.mark.asyncio
    async def test_get_next_pending_task(self, service: TaskService, mock_repository):
        """Test getting next pending task by priority."""
        # ARRANGE
        tasks = [
            Task(id="task_1", type=TaskType.BACKTEST.value, name="Task 1",
                 status=TaskStatus.PENDING.value, priority=TaskPriority.NORMAL.value,
                 params={}, created_by="test_user"),
            Task(id="task_2", type=TaskType.BACKTEST.value, name="Task 2",
                 status=TaskStatus.PENDING.value, priority=TaskPriority.HIGH.value,
                 params={}, created_by="test_user"),
        ]
        mock_repository.get_pending_tasks_by_priority = AsyncMock(return_value=tasks)

        # ACT
        result = await service.get_next_pending_task()

        # ASSERT
        assert result.id == "task_2"  # HIGH priority task should be first
        assert result.priority == TaskPriority.HIGH.value

    @pytest.mark.asyncio
    async def test_get_running_tasks_count(self, service: TaskService, mock_repository):
        """Test getting count of running tasks."""
        # ARRANGE
        mock_repository.count_tasks_by_status = AsyncMock(return_value=3)

        # ACT
        count = await service.get_running_tasks_count()

        # ASSERT
        assert count == 3
        mock_repository.count_tasks_by_status.assert_called_once_with(TaskStatus.RUNNING.value)

    @pytest.mark.asyncio
    async def test_get_tasks_by_user(self, service: TaskService, mock_repository):
        """Test getting tasks for specific user."""
        # ARRANGE
        tasks = [
            Task(id=f"task_{i}", type=TaskType.BACKTEST.value, name=f"Task {i}",
                 status=TaskStatus.PENDING.value, params={}, created_by="test_user")
            for i in range(2)
        ]
        mock_repository.get_tasks_by_user = AsyncMock(return_value=tasks)

        # ACT
        result = await service.get_user_tasks("test_user")

        # ASSERT
        assert len(result) == 2
        assert all(t.created_by == "test_user" for t in result)
        mock_repository.get_tasks_by_user.assert_called_once_with("test_user")

    # ==================== Task Validation Tests ====================

    @pytest.mark.asyncio
    async def test_validate_task_params_backtest(self, service: TaskService):
        """Test validating backtest task parameters."""
        # ARRANGE
        valid_params = {
            "strategy_id": "test_strategy",
            "dataset_id": "test_dataset"
        }

        # ACT
        result = service.validate_task_params(TaskType.BACKTEST.value, valid_params)

        # ASSERT
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_task_params_missing_required(self, service: TaskService):
        """Test validation fails with missing required params."""
        # ARRANGE
        invalid_params = {
            "strategy_id": "test_strategy"
            # Missing dataset_id
        }

        # ACT & ASSERT
        with pytest.raises(TaskValidationError, match="Missing required parameter"):
            service.validate_task_params(TaskType.BACKTEST.value, invalid_params)

    # ==================== Task Deletion Tests ====================

    @pytest.mark.asyncio
    async def test_delete_task_success(self, service: TaskService, mock_repository):
        """Test deleting a task."""
        # ARRANGE
        task = Task(
            id="task_123",
            type=TaskType.BACKTEST.value,
            name="Test Task",
            status=TaskStatus.COMPLETED.value,
            params={},
            created_by="test_user"
        )
        mock_repository.get_task_by_id = AsyncMock(return_value=task)
        mock_repository.delete_task = AsyncMock(return_value=True)

        # ACT
        result = await service.delete_task("task_123")

        # ASSERT
        assert result is True
        mock_repository.delete_task.assert_called_once_with("task_123")

    @pytest.mark.asyncio
    async def test_delete_running_task_error(self, service: TaskService, mock_repository):
        """Test cannot delete running task."""
        # ARRANGE
        task = Task(
            id="task_123",
            type=TaskType.BACKTEST.value,
            name="Test Task",
            status=TaskStatus.RUNNING.value,
            params={},
            created_by="test_user"
        )
        mock_repository.get_task_by_id = AsyncMock(return_value=task)

        # ACT & ASSERT
        with pytest.raises(TaskExecutionError, match="Cannot delete running task"):
            await service.delete_task("task_123")
