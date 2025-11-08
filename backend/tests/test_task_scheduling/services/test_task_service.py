"""
TDD Tests for Task Service

Comprehensive test coverage for:
- Task creation and validation with all task types
- Task lifecycle management (start, pause, resume, cancel, complete)
- Task queue management and priority handling
- Task status transitions and validation
- Error handling and recovery scenarios
- Task progress tracking with boundaries
- Data integrity and timestamp validation
- Edge cases and boundary conditions
- Concurrent task scenarios
- Logging and monitoring verification
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch, call
import asyncio

from app.database.models.task import Task, TaskType, TaskStatus, TaskPriority
from app.modules.task_scheduling.services.task_service import TaskService
from app.modules.task_scheduling.exceptions import (
    TaskNotFoundError,
    TaskValidationError,
    TaskExecutionError
)


class TestTaskServiceCreation:
    """Test TaskService task creation functionality."""

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
        """Test successful task creation with default values."""
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
        assert task.progress == 0.0
        mock_repository.create_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_task_with_custom_priority(self, service: TaskService, mock_repository, sample_task_data):
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
    async def test_create_task_with_urgent_priority(self, service: TaskService, mock_repository, sample_task_data):
        """Test creating task with urgent priority."""
        # ARRANGE
        task_data = {**sample_task_data, "priority": TaskPriority.URGENT.value}
        expected_task = Task(id="task_123", status=TaskStatus.PENDING.value, **task_data)
        mock_repository.create_task = AsyncMock(return_value=expected_task)

        # ACT
        task = await service.create_task(task_data)

        # ASSERT
        assert task.priority == TaskPriority.URGENT.value

    @pytest.mark.asyncio
    async def test_create_task_with_custom_status(self, service: TaskService, mock_repository, sample_task_data):
        """Test creating task with custom initial status."""
        # ARRANGE
        task_data = {**sample_task_data, "status": TaskStatus.RUNNING.value}
        expected_task = Task(id="task_123", **task_data)
        mock_repository.create_task = AsyncMock(return_value=expected_task)

        # ACT
        task = await service.create_task(task_data)

        # ASSERT
        assert task.status == TaskStatus.RUNNING.value

    @pytest.mark.asyncio
    async def test_create_task_missing_type(self, service: TaskService, sample_task_data):
        """Test task creation with missing required field: type."""
        # ARRANGE
        invalid_data = {**sample_task_data}
        del invalid_data["type"]

        # ACT & ASSERT
        with pytest.raises(TaskValidationError, match="Missing required field"):
            await service.create_task(invalid_data)

    @pytest.mark.asyncio
    async def test_create_task_missing_name(self, service: TaskService, sample_task_data):
        """Test task creation with missing required field: name."""
        # ARRANGE
        invalid_data = {**sample_task_data}
        del invalid_data["name"]

        # ACT & ASSERT
        with pytest.raises(TaskValidationError, match="Missing required field"):
            await service.create_task(invalid_data)

    @pytest.mark.asyncio
    async def test_create_task_missing_params(self, service: TaskService, sample_task_data):
        """Test task creation with missing required field: params."""
        # ARRANGE
        invalid_data = {**sample_task_data}
        del invalid_data["params"]

        # ACT & ASSERT
        with pytest.raises(TaskValidationError, match="Missing required field"):
            await service.create_task(invalid_data)

    @pytest.mark.asyncio
    async def test_create_task_missing_created_by(self, service: TaskService, sample_task_data):
        """Test task creation with missing required field: created_by."""
        # ARRANGE
        invalid_data = {**sample_task_data}
        del invalid_data["created_by"]

        # ACT & ASSERT
        with pytest.raises(TaskValidationError, match="Missing required field"):
            await service.create_task(invalid_data)

    @pytest.mark.asyncio
    async def test_create_task_invalid_type(self, service: TaskService, sample_task_data):
        """Test task creation with invalid task type."""
        # ARRANGE
        invalid_data = {**sample_task_data, "type": "INVALID_TYPE"}

        # ACT & ASSERT
        with pytest.raises(TaskValidationError, match="Invalid task type"):
            await service.create_task(invalid_data)

    @pytest.mark.asyncio
    async def test_create_backtest_task_missing_strategy_id(self, service: TaskService, sample_task_data):
        """Test backtest task creation with missing strategy_id parameter."""
        # ARRANGE
        task_data = {
            **sample_task_data,
            "params": {"dataset_id": "test_dataset"}  # Missing strategy_id
        }

        # ACT & ASSERT
        with pytest.raises(TaskValidationError, match="Missing required parameter"):
            await service.create_task(task_data)

    @pytest.mark.asyncio
    async def test_create_backtest_task_missing_dataset_id(self, service: TaskService, sample_task_data):
        """Test backtest task creation with missing dataset_id parameter."""
        # ARRANGE
        task_data = {
            **sample_task_data,
            "params": {"strategy_id": "test_strategy"}  # Missing dataset_id
        }

        # ACT & ASSERT
        with pytest.raises(TaskValidationError, match="Missing required parameter"):
            await service.create_task(task_data)

    @pytest.mark.asyncio
    async def test_create_optimization_task_valid(self, service: TaskService, mock_repository):
        """Test successful optimization task creation."""
        # ARRANGE
        task_data = {
            "type": TaskType.OPTIMIZATION.value,
            "name": "Optimization Task",
            "params": {"strategy_id": "test_strategy", "dataset_id": "test_dataset"},
            "created_by": "test_user"
        }
        expected_task = Task(id="task_123", status=TaskStatus.PENDING.value, **task_data)
        mock_repository.create_task = AsyncMock(return_value=expected_task)

        # ACT
        task = await service.create_task(task_data)

        # ASSERT
        assert task.type == TaskType.OPTIMIZATION.value

    @pytest.mark.asyncio
    async def test_create_data_import_task_valid(self, service: TaskService, mock_repository):
        """Test successful data import task creation."""
        # ARRANGE
        task_data = {
            "type": TaskType.DATA_IMPORT.value,
            "name": "Data Import Task",
            "params": {"file_path": "/path/to/file.csv"},
            "created_by": "test_user"
        }
        expected_task = Task(id="task_123", status=TaskStatus.PENDING.value, **task_data)
        mock_repository.create_task = AsyncMock(return_value=expected_task)

        # ACT
        task = await service.create_task(task_data)

        # ASSERT
        assert task.type == TaskType.DATA_IMPORT.value

    @pytest.mark.asyncio
    async def test_create_data_import_task_missing_file_path(self, service: TaskService):
        """Test data import task creation with missing file_path parameter."""
        # ARRANGE
        task_data = {
            "type": TaskType.DATA_IMPORT.value,
            "name": "Data Import Task",
            "params": {},  # Missing file_path
            "created_by": "test_user"
        }

        # ACT & ASSERT
        with pytest.raises(TaskValidationError, match="Missing required parameter"):
            await service.create_task(task_data)

    @pytest.mark.asyncio
    async def test_create_data_preprocessing_task_valid(self, service: TaskService, mock_repository):
        """Test successful data preprocessing task creation."""
        # ARRANGE
        task_data = {
            "type": TaskType.DATA_PREPROCESSING.value,
            "name": "Preprocessing Task",
            "params": {"dataset_id": "test_dataset"},
            "created_by": "test_user"
        }
        expected_task = Task(id="task_123", status=TaskStatus.PENDING.value, **task_data)
        mock_repository.create_task = AsyncMock(return_value=expected_task)

        # ACT
        task = await service.create_task(task_data)

        # ASSERT
        assert task.type == TaskType.DATA_PREPROCESSING.value

    @pytest.mark.asyncio
    async def test_create_factor_backtest_task_valid(self, service: TaskService, mock_repository):
        """Test successful factor backtest task creation."""
        # ARRANGE
        task_data = {
            "type": TaskType.FACTOR_BACKTEST.value,
            "name": "Factor Backtest Task",
            "params": {"factor_id": "test_factor", "dataset_id": "test_dataset"},
            "created_by": "test_user"
        }
        expected_task = Task(id="task_123", status=TaskStatus.PENDING.value, **task_data)
        mock_repository.create_task = AsyncMock(return_value=expected_task)

        # ACT
        task = await service.create_task(task_data)

        # ASSERT
        assert task.type == TaskType.FACTOR_BACKTEST.value

    @pytest.mark.asyncio
    async def test_create_custom_code_task_valid(self, service: TaskService, mock_repository):
        """Test successful custom code task creation."""
        # ARRANGE
        task_data = {
            "type": TaskType.CUSTOM_CODE.value,
            "name": "Custom Code Task",
            "params": {"code": "print('hello world')"},
            "created_by": "test_user"
        }
        expected_task = Task(id="task_123", status=TaskStatus.PENDING.value, **task_data)
        mock_repository.create_task = AsyncMock(return_value=expected_task)

        # ACT
        task = await service.create_task(task_data)

        # ASSERT
        assert task.type == TaskType.CUSTOM_CODE.value

    @pytest.mark.asyncio
    async def test_create_custom_code_task_missing_code(self, service: TaskService):
        """Test custom code task creation with missing code parameter."""
        # ARRANGE
        task_data = {
            "type": TaskType.CUSTOM_CODE.value,
            "name": "Custom Code Task",
            "params": {},  # Missing code
            "created_by": "test_user"
        }

        # ACT & ASSERT
        with pytest.raises(TaskValidationError, match="Missing required parameter"):
            await service.create_task(task_data)

    @pytest.mark.asyncio
    async def test_create_task_with_extra_params_in_params(self, service: TaskService, mock_repository):
        """Test task creation with extra parameters in params field."""
        # ARRANGE
        task_data = {
            "type": TaskType.BACKTEST.value,
            "name": "Test Task",
            "params": {
                "strategy_id": "test_strategy",
                "dataset_id": "test_dataset",
                "extra_param": "extra_value",
                "nested": {"data": "value"}
            },
            "created_by": "test_user"
        }
        expected_task = Task(id="task_123", status=TaskStatus.PENDING.value, **task_data)
        mock_repository.create_task = AsyncMock(return_value=expected_task)

        # ACT
        task = await service.create_task(task_data)

        # ASSERT
        assert task.id == "task_123"

    @pytest.mark.asyncio
    async def test_create_task_with_long_name(self, service: TaskService, mock_repository, sample_task_data):
        """Test task creation with very long name."""
        # ARRANGE
        long_name = "A" * 255
        task_data = {**sample_task_data, "name": long_name}
        expected_task = Task(id="task_123", **task_data)
        mock_repository.create_task = AsyncMock(return_value=expected_task)

        # ACT
        task = await service.create_task(task_data)

        # ASSERT
        assert task.name == long_name

    @pytest.mark.asyncio
    async def test_create_task_with_empty_params(self, service: TaskService, mock_repository):
        """Test task creation with empty params (if allowed by task type)."""
        # ARRANGE
        task_data = {
            "type": "UNKNOWN_TYPE",  # Type with no param requirements
            "name": "Task with no params",
            "params": {},
            "created_by": "test_user"
        }

        # ACT & ASSERT
        with pytest.raises(TaskValidationError):
            await service.create_task(task_data)

    @pytest.mark.asyncio
    async def test_create_task_logging(self, service: TaskService, mock_repository, sample_task_data):
        """Test that task creation is properly logged."""
        # ARRANGE
        expected_task = Task(id="task_123", **sample_task_data)
        mock_repository.create_task = AsyncMock(return_value=expected_task)

        with patch('app.modules.task_scheduling.services.task_service.logger') as mock_logger:
            # ACT
            await service.create_task(sample_task_data)

            # ASSERT
            mock_logger.info.assert_called()


class TestTaskServiceRetrieval:
    """Test TaskService task retrieval functionality."""

    @pytest.fixture
    def mock_repository(self, mocker):
        """Create a mock TaskRepository."""
        return mocker.Mock()

    @pytest.fixture
    def service(self, mock_repository):
        """Create a TaskService instance with mocked repository."""
        return TaskService(mock_repository)

    # ==================== Task Retrieval Tests ====================

    @pytest.mark.asyncio
    async def test_get_task_by_id_success(self, service: TaskService, mock_repository):
        """Test retrieving task by ID successfully."""
        # ARRANGE
        expected_task = Task(
            id="task_123",
            type=TaskType.BACKTEST.value,
            name="Test Task",
            status=TaskStatus.PENDING.value,
            params={"strategy_id": "test_strategy"},
            created_by="test_user"
        )
        mock_repository.get_task_by_id = AsyncMock(return_value=expected_task)

        # ACT
        task = await service.get_task("task_123")

        # ASSERT
        assert task.id == "task_123"
        assert task.name == "Test Task"
        mock_repository.get_task_by_id.assert_called_once_with("task_123")

    @pytest.mark.asyncio
    async def test_get_task_not_found(self, service: TaskService, mock_repository):
        """Test retrieving non-existent task raises error."""
        # ARRANGE
        mock_repository.get_task_by_id = AsyncMock(return_value=None)

        # ACT & ASSERT
        with pytest.raises(TaskNotFoundError, match="Task not found"):
            await service.get_task("non_existent_id")

    @pytest.mark.asyncio
    async def test_get_task_with_empty_id(self, service: TaskService, mock_repository):
        """Test retrieving task with empty ID."""
        # ARRANGE
        mock_repository.get_task_by_id = AsyncMock(return_value=None)

        # ACT & ASSERT
        with pytest.raises(TaskNotFoundError):
            await service.get_task("")

    @pytest.mark.asyncio
    async def test_list_tasks_default_pagination(self, service: TaskService, mock_repository):
        """Test listing tasks with default pagination."""
        # ARRANGE
        tasks = [
            Task(id=f"task_{i}", type=TaskType.BACKTEST.value, name=f"Task {i}",
                 status=TaskStatus.PENDING.value, params={}, created_by="test_user")
            for i in range(5)
        ]
        mock_repository.get_tasks = AsyncMock(return_value=tasks)

        # ACT
        result = await service.list_tasks()

        # ASSERT
        assert len(result) == 5
        mock_repository.get_tasks.assert_called_once_with(skip=0, limit=100)

    @pytest.mark.asyncio
    async def test_list_tasks_with_custom_pagination(self, service: TaskService, mock_repository):
        """Test listing tasks with custom skip and limit."""
        # ARRANGE
        tasks = [
            Task(id=f"task_{i}", type=TaskType.BACKTEST.value, name=f"Task {i}",
                 status=TaskStatus.PENDING.value, params={}, created_by="test_user")
            for i in range(3)
        ]
        mock_repository.get_tasks = AsyncMock(return_value=tasks)

        # ACT
        result = await service.list_tasks(skip=10, limit=50)

        # ASSERT
        assert len(result) == 3
        mock_repository.get_tasks.assert_called_once_with(skip=10, limit=50)

    @pytest.mark.asyncio
    async def test_list_tasks_empty_result(self, service: TaskService, mock_repository):
        """Test listing tasks with no results."""
        # ARRANGE
        mock_repository.get_tasks = AsyncMock(return_value=[])

        # ACT
        result = await service.list_tasks()

        # ASSERT
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_list_tasks_large_limit(self, service: TaskService, mock_repository):
        """Test listing tasks with large limit."""
        # ARRANGE
        tasks = [
            Task(id=f"task_{i}", type=TaskType.BACKTEST.value, name=f"Task {i}",
                 status=TaskStatus.PENDING.value, params={}, created_by="test_user")
            for i in range(10)
        ]
        mock_repository.get_tasks = AsyncMock(return_value=tasks)

        # ACT
        result = await service.list_tasks(skip=0, limit=1000)

        # ASSERT
        assert len(result) == 10
        mock_repository.get_tasks.assert_called_once_with(skip=0, limit=1000)

    @pytest.mark.asyncio
    async def test_get_user_tasks_success(self, service: TaskService, mock_repository):
        """Test getting tasks for a specific user."""
        # ARRANGE
        tasks = [
            Task(id=f"task_{i}", type=TaskType.BACKTEST.value, name=f"Task {i}",
                 status=TaskStatus.PENDING.value, params={}, created_by="test_user")
            for i in range(3)
        ]
        mock_repository.get_tasks_by_user = AsyncMock(return_value=tasks)

        # ACT
        result = await service.get_user_tasks("test_user")

        # ASSERT
        assert len(result) == 3
        assert all(t.created_by == "test_user" for t in result)
        mock_repository.get_tasks_by_user.assert_called_once_with("test_user")

    @pytest.mark.asyncio
    async def test_get_user_tasks_empty(self, service: TaskService, mock_repository):
        """Test getting tasks for user with no tasks."""
        # ARRANGE
        mock_repository.get_tasks_by_user = AsyncMock(return_value=[])

        # ACT
        result = await service.get_user_tasks("user_with_no_tasks")

        # ASSERT
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_get_user_tasks_multiple_users(self, service: TaskService, mock_repository):
        """Test getting tasks filters correctly by user."""
        # ARRANGE
        tasks = [
            Task(id="task_1", type=TaskType.BACKTEST.value, name="Task 1",
                 status=TaskStatus.PENDING.value, params={}, created_by="user_a"),
            Task(id="task_2", type=TaskType.BACKTEST.value, name="Task 2",
                 status=TaskStatus.PENDING.value, params={}, created_by="user_a")
        ]
        mock_repository.get_tasks_by_user = AsyncMock(return_value=tasks)

        # ACT
        result = await service.get_user_tasks("user_a")

        # ASSERT
        assert len(result) == 2
        assert all(t.created_by == "user_a" for t in result)


class TestTaskServiceLifecycle:
    """Test TaskService task lifecycle management."""

    @pytest.fixture
    def mock_repository(self, mocker):
        """Create a mock TaskRepository."""
        return mocker.Mock()

    @pytest.fixture
    def service(self, mock_repository):
        """Create a TaskService instance with mocked repository."""
        return TaskService(mock_repository)

    # ==================== Task Lifecycle Tests ====================

    @pytest.mark.asyncio
    async def test_start_task_success(self, service: TaskService, mock_repository):
        """Test starting a pending task successfully."""
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
    async def test_start_task_not_pending(self, service: TaskService, mock_repository):
        """Test starting task that is not pending raises error."""
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
        with pytest.raises(TaskExecutionError, match="Cannot start task with status"):
            await service.start_task("task_123")

    @pytest.mark.asyncio
    async def test_start_task_completed_status(self, service: TaskService, mock_repository):
        """Test starting a completed task raises error."""
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

        # ACT & ASSERT
        with pytest.raises(TaskExecutionError, match="Task must be in PENDING status"):
            await service.start_task("task_123")

    @pytest.mark.asyncio
    async def test_start_task_not_found(self, service: TaskService, mock_repository):
        """Test starting non-existent task raises error."""
        # ARRANGE
        mock_repository.get_task_by_id = AsyncMock(return_value=None)

        # ACT & ASSERT
        with pytest.raises(TaskNotFoundError):
            await service.start_task("non_existent_id")

    @pytest.mark.asyncio
    async def test_pause_task_success(self, service: TaskService, mock_repository):
        """Test pausing a running task successfully."""
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
    async def test_pause_task_not_running(self, service: TaskService, mock_repository):
        """Test pausing task that is not running raises error."""
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

        # ACT & ASSERT
        with pytest.raises(TaskExecutionError, match="Cannot pause task with status"):
            await service.pause_task("task_123")

    @pytest.mark.asyncio
    async def test_pause_task_completed(self, service: TaskService, mock_repository):
        """Test pausing a completed task raises error."""
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

        # ACT & ASSERT
        with pytest.raises(TaskExecutionError, match="Task must be in RUNNING status"):
            await service.pause_task("task_123")

    @pytest.mark.asyncio
    async def test_resume_task_success(self, service: TaskService, mock_repository):
        """Test resuming a paused task successfully."""
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
    async def test_resume_task_not_paused(self, service: TaskService, mock_repository):
        """Test resuming task that is not paused raises error."""
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
        with pytest.raises(TaskExecutionError, match="Cannot resume task with status"):
            await service.resume_task("task_123")

    @pytest.mark.asyncio
    async def test_resume_task_pending(self, service: TaskService, mock_repository):
        """Test resuming a pending task raises error."""
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

        # ACT & ASSERT
        with pytest.raises(TaskExecutionError, match="Task must be in PAUSED status"):
            await service.resume_task("task_123")

    @pytest.mark.asyncio
    async def test_cancel_task_pending(self, service: TaskService, mock_repository):
        """Test cancelling a pending task."""
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
        result = await service.cancel_task("task_123")

        # ASSERT
        assert result.status == TaskStatus.CANCELLED.value
        mock_repository.update_task_status.assert_called_once_with("task_123", TaskStatus.CANCELLED.value)

    @pytest.mark.asyncio
    async def test_cancel_task_running(self, service: TaskService, mock_repository):
        """Test cancelling a running task."""
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

    @pytest.mark.asyncio
    async def test_cancel_task_paused(self, service: TaskService, mock_repository):
        """Test cancelling a paused task."""
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
        result = await service.cancel_task("task_123")

        # ASSERT
        assert result.status == TaskStatus.CANCELLED.value

    @pytest.mark.asyncio
    async def test_cancel_task_completed(self, service: TaskService, mock_repository):
        """Test cancelling a completed task raises error."""
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

        # ACT & ASSERT
        with pytest.raises(TaskExecutionError, match="Task is already in a terminal state"):
            await service.cancel_task("task_123")

    @pytest.mark.asyncio
    async def test_cancel_task_failed(self, service: TaskService, mock_repository):
        """Test cancelling a failed task raises error."""
        # ARRANGE
        task = Task(
            id="task_123",
            type=TaskType.BACKTEST.value,
            name="Test Task",
            status=TaskStatus.FAILED.value,
            params={},
            created_by="test_user"
        )
        mock_repository.get_task_by_id = AsyncMock(return_value=task)

        # ACT & ASSERT
        with pytest.raises(TaskExecutionError, match="Task is already in a terminal state"):
            await service.cancel_task("task_123")

    @pytest.mark.asyncio
    async def test_cancel_task_already_cancelled(self, service: TaskService, mock_repository):
        """Test cancelling an already cancelled task raises error."""
        # ARRANGE
        task = Task(
            id="task_123",
            type=TaskType.BACKTEST.value,
            name="Test Task",
            status=TaskStatus.CANCELLED.value,
            params={},
            created_by="test_user"
        )
        mock_repository.get_task_by_id = AsyncMock(return_value=task)

        # ACT & ASSERT
        with pytest.raises(TaskExecutionError, match="Task is already in a terminal state"):
            await service.cancel_task("task_123")

    @pytest.mark.asyncio
    async def test_complete_task_with_result(self, service: TaskService, mock_repository):
        """Test completing a task with result data."""
        # ARRANGE
        task = Task(
            id="task_123",
            type=TaskType.BACKTEST.value,
            name="Test Task",
            status=TaskStatus.RUNNING.value,
            params={},
            created_by="test_user"
        )
        result_data = {"total_return": 0.15, "sharpe_ratio": 1.5, "max_drawdown": -0.10}
        mock_repository.get_task_by_id = AsyncMock(return_value=task)
        mock_repository.update_task = AsyncMock(return_value=task)

        # ACT
        result = await service.complete_task("task_123", result_data)

        # ASSERT
        assert result.status == TaskStatus.COMPLETED.value
        assert result.progress == 100.0
        mock_repository.update_task.assert_called_once()
        call_args = mock_repository.update_task.call_args[0]
        assert call_args[0] == "task_123"
        assert call_args[1]["status"] == TaskStatus.COMPLETED.value
        assert call_args[1]["result"] == result_data
        assert call_args[1]["progress"] == 100.0

    @pytest.mark.asyncio
    async def test_complete_task_without_result(self, service: TaskService, mock_repository):
        """Test completing a task without result data."""
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
        result = await service.complete_task("task_123")

        # ASSERT
        assert result.status == TaskStatus.COMPLETED.value
        call_args = mock_repository.update_task.call_args[0]
        assert call_args[1]["result"] == {}

    @pytest.mark.asyncio
    async def test_complete_task_with_none_result(self, service: TaskService, mock_repository):
        """Test completing a task with None result data."""
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
        result = await service.complete_task("task_123", None)

        # ASSERT
        assert result.status == TaskStatus.COMPLETED.value
        call_args = mock_repository.update_task.call_args[0]
        assert call_args[1]["result"] == {}

    @pytest.mark.asyncio
    async def test_fail_task_with_error_message(self, service: TaskService, mock_repository):
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
        assert result.error == error_message
        mock_repository.update_task.assert_called_once()
        call_args = mock_repository.update_task.call_args[0]
        assert call_args[1]["status"] == TaskStatus.FAILED.value
        assert call_args[1]["error"] == error_message

    @pytest.mark.asyncio
    async def test_fail_task_with_long_error_message(self, service: TaskService, mock_repository):
        """Test marking task as failed with very long error message."""
        # ARRANGE
        task = Task(
            id="task_123",
            type=TaskType.BACKTEST.value,
            name="Test Task",
            status=TaskStatus.RUNNING.value,
            params={},
            created_by="test_user"
        )
        long_error = "E" * 1000
        mock_repository.get_task_by_id = AsyncMock(return_value=task)
        mock_repository.update_task = AsyncMock(return_value=task)

        # ACT
        result = await service.fail_task("task_123", long_error)

        # ASSERT
        assert result.status == TaskStatus.FAILED.value
        call_args = mock_repository.update_task.call_args[0]
        assert call_args[1]["error"] == long_error

    @pytest.mark.asyncio
    async def test_fail_task_not_found(self, service: TaskService, mock_repository):
        """Test failing a non-existent task raises error."""
        # ARRANGE
        mock_repository.get_task_by_id = AsyncMock(return_value=None)

        # ACT & ASSERT
        with pytest.raises(TaskNotFoundError):
            await service.fail_task("non_existent_id", "Some error")


class TestTaskServiceProgress:
    """Test TaskService progress tracking functionality."""

    @pytest.fixture
    def mock_repository(self, mocker):
        """Create a mock TaskRepository."""
        return mocker.Mock()

    @pytest.fixture
    def service(self, mock_repository):
        """Create a TaskService instance with mocked repository."""
        return TaskService(mock_repository)

    # ==================== Task Progress Tests ====================

    @pytest.mark.asyncio
    async def test_update_progress_with_all_parameters(self, service: TaskService, mock_repository):
        """Test updating task progress with all optional parameters."""
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
            progress=50.5,
            current_step="Processing data",
            eta=120
        )

        # ASSERT
        mock_repository.update_task.assert_called_once()
        call_args = mock_repository.update_task.call_args[0]
        assert call_args[1]["progress"] == 50.5
        assert call_args[1]["current_step"] == "Processing data"
        assert call_args[1]["eta"] == 120

    @pytest.mark.asyncio
    async def test_update_progress_only_progress(self, service: TaskService, mock_repository):
        """Test updating task progress with only progress value."""
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
        result = await service.update_progress("task_123", progress=25.0)

        # ASSERT
        call_args = mock_repository.update_task.call_args[0]
        assert call_args[1]["progress"] == 25.0
        assert "current_step" not in call_args[1]
        assert "eta" not in call_args[1]

    @pytest.mark.asyncio
    async def test_update_progress_with_current_step(self, service: TaskService, mock_repository):
        """Test updating progress with current step."""
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
            progress=75.0,
            current_step="Backtesting strategy"
        )

        # ASSERT
        call_args = mock_repository.update_task.call_args[0]
        assert call_args[1]["progress"] == 75.0
        assert call_args[1]["current_step"] == "Backtesting strategy"

    @pytest.mark.asyncio
    async def test_update_progress_with_eta(self, service: TaskService, mock_repository):
        """Test updating progress with ETA."""
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
            progress=60.0,
            eta=300
        )

        # ASSERT
        call_args = mock_repository.update_task.call_args[0]
        assert call_args[1]["progress"] == 60.0
        assert call_args[1]["eta"] == 300

    @pytest.mark.asyncio
    async def test_update_progress_zero_progress(self, service: TaskService, mock_repository):
        """Test updating progress to 0."""
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
        result = await service.update_progress("task_123", progress=0.0)

        # ASSERT
        call_args = mock_repository.update_task.call_args[0]
        assert call_args[1]["progress"] == 0.0

    @pytest.mark.asyncio
    async def test_update_progress_hundred_percent(self, service: TaskService, mock_repository):
        """Test updating progress to 100 percent."""
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
        result = await service.update_progress("task_123", progress=100.0)

        # ASSERT
        call_args = mock_repository.update_task.call_args[0]
        assert call_args[1]["progress"] == 100.0

    @pytest.mark.asyncio
    async def test_update_progress_fractional_value(self, service: TaskService, mock_repository):
        """Test updating progress with fractional value."""
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
        result = await service.update_progress("task_123", progress=33.333)

        # ASSERT
        call_args = mock_repository.update_task.call_args[0]
        assert call_args[1]["progress"] == 33.333

    @pytest.mark.asyncio
    async def test_update_progress_zero_eta(self, service: TaskService, mock_repository):
        """Test updating progress with zero ETA."""
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
        result = await service.update_progress("task_123", progress=99.0, eta=0)

        # ASSERT
        call_args = mock_repository.update_task.call_args[0]
        assert call_args[1]["eta"] == 0

    @pytest.mark.asyncio
    async def test_update_progress_task_not_found(self, service: TaskService, mock_repository):
        """Test updating progress for non-existent task."""
        # ARRANGE
        mock_repository.get_task_by_id = AsyncMock(return_value=None)

        # ACT & ASSERT
        with pytest.raises(TaskNotFoundError):
            await service.update_progress("non_existent_id", progress=50.0)


class TestTaskServiceQueueManagement:
    """Test TaskService queue and priority management."""

    @pytest.fixture
    def mock_repository(self, mocker):
        """Create a mock TaskRepository."""
        return mocker.Mock()

    @pytest.fixture
    def service(self, mock_repository):
        """Create a TaskService instance with mocked repository."""
        return TaskService(mock_repository)

    # ==================== Task Queue Management Tests ====================

    @pytest.mark.asyncio
    async def test_get_next_pending_task_by_priority(self, service: TaskService, mock_repository):
        """Test getting next pending task returns highest priority task."""
        # ARRANGE
        tasks = [
            Task(id="task_1", type=TaskType.BACKTEST.value, name="Task 1",
                 status=TaskStatus.PENDING.value, priority=TaskPriority.NORMAL.value,
                 params={}, created_by="test_user"),
            Task(id="task_2", type=TaskType.BACKTEST.value, name="Task 2",
                 status=TaskStatus.PENDING.value, priority=TaskPriority.HIGH.value,
                 params={}, created_by="test_user"),
            Task(id="task_3", type=TaskType.BACKTEST.value, name="Task 3",
                 status=TaskStatus.PENDING.value, priority=TaskPriority.URGENT.value,
                 params={}, created_by="test_user"),
        ]
        mock_repository.get_pending_tasks_by_priority = AsyncMock(return_value=tasks)

        # ACT
        result = await service.get_next_pending_task()

        # ASSERT
        assert result.id == "task_3"
        assert result.priority == TaskPriority.URGENT.value

    @pytest.mark.asyncio
    async def test_get_next_pending_task_single_task(self, service: TaskService, mock_repository):
        """Test getting next pending task when only one task exists."""
        # ARRANGE
        tasks = [
            Task(id="task_1", type=TaskType.BACKTEST.value, name="Task 1",
                 status=TaskStatus.PENDING.value, priority=TaskPriority.NORMAL.value,
                 params={}, created_by="test_user")
        ]
        mock_repository.get_pending_tasks_by_priority = AsyncMock(return_value=tasks)

        # ACT
        result = await service.get_next_pending_task()

        # ASSERT
        assert result.id == "task_1"

    @pytest.mark.asyncio
    async def test_get_next_pending_task_no_pending_tasks(self, service: TaskService, mock_repository):
        """Test getting next pending task when no pending tasks exist."""
        # ARRANGE
        mock_repository.get_pending_tasks_by_priority = AsyncMock(return_value=[])

        # ACT
        result = await service.get_next_pending_task()

        # ASSERT
        assert result is None

    @pytest.mark.asyncio
    async def test_get_next_pending_task_all_low_priority(self, service: TaskService, mock_repository):
        """Test getting next pending task returns highest among low priority tasks."""
        # ARRANGE
        tasks = [
            Task(id="task_1", type=TaskType.BACKTEST.value, name="Task 1",
                 status=TaskStatus.PENDING.value, priority=TaskPriority.LOW.value,
                 params={}, created_by="test_user"),
            Task(id="task_2", type=TaskType.BACKTEST.value, name="Task 2",
                 status=TaskStatus.PENDING.value, priority=TaskPriority.LOW.value,
                 params={}, created_by="test_user"),
        ]
        mock_repository.get_pending_tasks_by_priority = AsyncMock(return_value=tasks)

        # ACT
        result = await service.get_next_pending_task()

        # ASSERT
        assert result is not None
        assert result.priority == TaskPriority.LOW.value

    @pytest.mark.asyncio
    async def test_get_running_tasks_count(self, service: TaskService, mock_repository):
        """Test getting count of running tasks."""
        # ARRANGE
        mock_repository.count_tasks_by_status = AsyncMock(return_value=5)

        # ACT
        count = await service.get_running_tasks_count()

        # ASSERT
        assert count == 5
        mock_repository.count_tasks_by_status.assert_called_once_with(TaskStatus.RUNNING.value)

    @pytest.mark.asyncio
    async def test_get_running_tasks_count_zero(self, service: TaskService, mock_repository):
        """Test getting count of running tasks when none are running."""
        # ARRANGE
        mock_repository.count_tasks_by_status = AsyncMock(return_value=0)

        # ACT
        count = await service.get_running_tasks_count()

        # ASSERT
        assert count == 0

    @pytest.mark.asyncio
    async def test_get_running_tasks_count_many(self, service: TaskService, mock_repository):
        """Test getting count when many tasks are running."""
        # ARRANGE
        mock_repository.count_tasks_by_status = AsyncMock(return_value=100)

        # ACT
        count = await service.get_running_tasks_count()

        # ASSERT
        assert count == 100


class TestTaskServiceValidation:
    """Test TaskService parameter validation."""

    @pytest.fixture
    def mock_repository(self, mocker):
        """Create a mock TaskRepository."""
        return mocker.Mock()

    @pytest.fixture
    def service(self, mock_repository):
        """Create a TaskService instance with mocked repository."""
        return TaskService(mock_repository)

    # ==================== Task Validation Tests ====================

    @pytest.mark.asyncio
    async def test_validate_task_params_backtest_valid(self, service: TaskService):
        """Test validating valid backtest task parameters."""
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
    async def test_validate_task_params_backtest_missing_strategy(self, service: TaskService):
        """Test validation fails with missing strategy_id."""
        # ARRANGE
        invalid_params = {"dataset_id": "test_dataset"}

        # ACT & ASSERT
        with pytest.raises(TaskValidationError, match="Missing required parameter"):
            service.validate_task_params(TaskType.BACKTEST.value, invalid_params)

    @pytest.mark.asyncio
    async def test_validate_task_params_backtest_missing_dataset(self, service: TaskService):
        """Test validation fails with missing dataset_id."""
        # ARRANGE
        invalid_params = {"strategy_id": "test_strategy"}

        # ACT & ASSERT
        with pytest.raises(TaskValidationError, match="Missing required parameter"):
            service.validate_task_params(TaskType.BACKTEST.value, invalid_params)

    @pytest.mark.asyncio
    async def test_validate_task_params_backtest_extra_params(self, service: TaskService):
        """Test validation passes with extra parameters."""
        # ARRANGE
        valid_params = {
            "strategy_id": "test_strategy",
            "dataset_id": "test_dataset",
            "extra_param": "extra_value"
        }

        # ACT
        result = service.validate_task_params(TaskType.BACKTEST.value, valid_params)

        # ASSERT
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_task_params_optimization_valid(self, service: TaskService):
        """Test validating valid optimization task parameters."""
        # ARRANGE
        valid_params = {
            "strategy_id": "test_strategy",
            "dataset_id": "test_dataset"
        }

        # ACT
        result = service.validate_task_params(TaskType.OPTIMIZATION.value, valid_params)

        # ASSERT
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_task_params_data_import_valid(self, service: TaskService):
        """Test validating valid data import task parameters."""
        # ARRANGE
        valid_params = {"file_path": "/path/to/file.csv"}

        # ACT
        result = service.validate_task_params(TaskType.DATA_IMPORT.value, valid_params)

        # ASSERT
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_task_params_data_preprocessing_valid(self, service: TaskService):
        """Test validating valid data preprocessing task parameters."""
        # ARRANGE
        valid_params = {"dataset_id": "test_dataset"}

        # ACT
        result = service.validate_task_params(TaskType.DATA_PREPROCESSING.value, valid_params)

        # ASSERT
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_task_params_factor_backtest_valid(self, service: TaskService):
        """Test validating valid factor backtest task parameters."""
        # ARRANGE
        valid_params = {"factor_id": "test_factor", "dataset_id": "test_dataset"}

        # ACT
        result = service.validate_task_params(TaskType.FACTOR_BACKTEST.value, valid_params)

        # ASSERT
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_task_params_custom_code_valid(self, service: TaskService):
        """Test validating valid custom code task parameters."""
        # ARRANGE
        valid_params = {"code": "print('hello')"}

        # ACT
        result = service.validate_task_params(TaskType.CUSTOM_CODE.value, valid_params)

        # ASSERT
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_task_params_empty_params(self, service: TaskService):
        """Test validation with empty params for type with requirements."""
        # ARRANGE
        empty_params = {}

        # ACT & ASSERT
        with pytest.raises(TaskValidationError, match="Missing required parameter"):
            service.validate_task_params(TaskType.BACKTEST.value, empty_params)

    def test_validate_task_params_no_requirements(self, service: TaskService):
        """Test validation for task type with no parameter requirements."""
        # This tests a hypothetical case where a task type isn't in TASK_PARAM_REQUIREMENTS
        # Use a fake task type that doesn't have requirements defined
        # ARRANGE
        fake_task_type = "UNKNOWN_TASK_TYPE"

        # ACT - Validate a task type not in TASK_PARAM_REQUIREMENTS
        result = service.validate_task_params(fake_task_type, {})

        # ASSERT - Should return True since no requirements are defined
        assert result is True


class TestTaskServiceDeletion:
    """Test TaskService task deletion functionality."""

    @pytest.fixture
    def mock_repository(self, mocker):
        """Create a mock TaskRepository."""
        return mocker.Mock()

    @pytest.fixture
    def service(self, mock_repository):
        """Create a TaskService instance with mocked repository."""
        return TaskService(mock_repository)

    # ==================== Task Deletion Tests ====================

    @pytest.mark.asyncio
    async def test_delete_task_completed(self, service: TaskService, mock_repository):
        """Test deleting a completed task."""
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
    async def test_delete_task_cancelled(self, service: TaskService, mock_repository):
        """Test deleting a cancelled task."""
        # ARRANGE
        task = Task(
            id="task_123",
            type=TaskType.BACKTEST.value,
            name="Test Task",
            status=TaskStatus.CANCELLED.value,
            params={},
            created_by="test_user"
        )
        mock_repository.get_task_by_id = AsyncMock(return_value=task)
        mock_repository.delete_task = AsyncMock(return_value=True)

        # ACT
        result = await service.delete_task("task_123")

        # ASSERT
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_task_failed(self, service: TaskService, mock_repository):
        """Test deleting a failed task."""
        # ARRANGE
        task = Task(
            id="task_123",
            type=TaskType.BACKTEST.value,
            name="Test Task",
            status=TaskStatus.FAILED.value,
            params={},
            created_by="test_user"
        )
        mock_repository.get_task_by_id = AsyncMock(return_value=task)
        mock_repository.delete_task = AsyncMock(return_value=True)

        # ACT
        result = await service.delete_task("task_123")

        # ASSERT
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_task_pending(self, service: TaskService, mock_repository):
        """Test deleting a pending task."""
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
        mock_repository.delete_task = AsyncMock(return_value=True)

        # ACT
        result = await service.delete_task("task_123")

        # ASSERT
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_task_paused(self, service: TaskService, mock_repository):
        """Test deleting a paused task."""
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
        mock_repository.delete_task = AsyncMock(return_value=True)

        # ACT
        result = await service.delete_task("task_123")

        # ASSERT
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_running_task_error(self, service: TaskService, mock_repository):
        """Test cannot delete a running task."""
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

    @pytest.mark.asyncio
    async def test_delete_task_not_found(self, service: TaskService, mock_repository):
        """Test deleting non-existent task raises error."""
        # ARRANGE
        mock_repository.get_task_by_id = AsyncMock(return_value=None)

        # ACT & ASSERT
        with pytest.raises(TaskNotFoundError):
            await service.delete_task("non_existent_id")

    @pytest.mark.asyncio
    async def test_delete_task_repository_returns_false(self, service: TaskService, mock_repository):
        """Test delete task when repository returns False."""
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
        mock_repository.delete_task = AsyncMock(return_value=False)

        # ACT
        result = await service.delete_task("task_123")

        # ASSERT
        assert result is False


class TestTaskServiceEdgeCases:
    """Test TaskService edge cases and boundary conditions."""

    @pytest.fixture
    def mock_repository(self, mocker):
        """Create a mock TaskRepository."""
        return mocker.Mock()

    @pytest.fixture
    def service(self, mock_repository):
        """Create a TaskService instance with mocked repository."""
        return TaskService(mock_repository)

    # ==================== Edge Cases and Boundary Tests ====================

    @pytest.mark.asyncio
    async def test_create_task_with_complex_nested_params(self, service: TaskService, mock_repository):
        """Test creating task with complex nested parameters."""
        # ARRANGE
        task_data = {
            "type": TaskType.BACKTEST.value,
            "name": "Complex Task",
            "params": {
                "strategy_id": "test_strategy",
                "dataset_id": "test_dataset",
                "nested": {
                    "level_2": {
                        "level_3": ["a", "b", "c"]
                    }
                }
            },
            "created_by": "test_user"
        }
        expected_task = Task(id="task_123", status=TaskStatus.PENDING.value, **task_data)
        mock_repository.create_task = AsyncMock(return_value=expected_task)

        # ACT
        task = await service.create_task(task_data)

        # ASSERT
        assert task.id == "task_123"

    @pytest.mark.asyncio
    async def test_create_task_with_special_characters_in_name(self, service: TaskService, mock_repository):
        """Test creating task with special characters in name."""
        # ARRANGE
        task_data = {
            "type": TaskType.BACKTEST.value,
            "name": "Task with special chars: !@#$%^&*()",
            "params": {"strategy_id": "test", "dataset_id": "test"},
            "created_by": "test_user"
        }
        expected_task = Task(id="task_123", **task_data)
        mock_repository.create_task = AsyncMock(return_value=expected_task)

        # ACT
        task = await service.create_task(task_data)

        # ASSERT
        assert "special chars" in task.name

    @pytest.mark.asyncio
    async def test_create_task_with_unicode_characters(self, service: TaskService, mock_repository):
        """Test creating task with unicode characters."""
        # ARRANGE
        task_data = {
            "type": TaskType.BACKTEST.value,
            "name": "任务 タスク مهمة",
            "params": {"strategy_id": "test", "dataset_id": "test"},
            "created_by": "test_user"
        }
        expected_task = Task(id="task_123", **task_data)
        mock_repository.create_task = AsyncMock(return_value=expected_task)

        # ACT
        task = await service.create_task(task_data)

        # ASSERT
        assert task.name == "任务 タスク مهمة"

    @pytest.mark.asyncio
    async def test_status_transition_sequence(self, service: TaskService, mock_repository):
        """Test complete status transition sequence."""
        # ARRANGE - Create tasks with different states
        pending_task = Task(
            id="task_123",
            type=TaskType.BACKTEST.value,
            name="Test Task",
            status=TaskStatus.PENDING.value,
            params={},
            created_by="test_user"
        )
        running_task = Task(
            id="task_123",
            type=TaskType.BACKTEST.value,
            name="Test Task",
            status=TaskStatus.RUNNING.value,
            params={},
            created_by="test_user"
        )
        paused_task = Task(
            id="task_123",
            type=TaskType.BACKTEST.value,
            name="Test Task",
            status=TaskStatus.PAUSED.value,
            params={},
            created_by="test_user"
        )

        # Setup mock to return correct task state for each call
        task_states = [pending_task, running_task, paused_task, running_task]
        state_index = [0]

        async def get_task_side_effect(task_id):
            result = task_states[state_index[0]]
            state_index[0] += 1
            return result

        mock_repository.get_task_by_id = AsyncMock(side_effect=get_task_side_effect)
        mock_repository.update_task_status = AsyncMock(return_value=running_task)

        # ACT - Pending -> Running
        result = await service.start_task("task_123")
        assert result.status == TaskStatus.RUNNING.value

        # ACT - Running -> Paused
        result = await service.pause_task("task_123")
        assert result.status == TaskStatus.PAUSED.value

        # ACT - Paused -> Running
        result = await service.resume_task("task_123")
        assert result.status == TaskStatus.RUNNING.value

        # ASSERT - All transitions verified
        assert mock_repository.update_task_status.call_count == 3

    @pytest.mark.asyncio
    async def test_large_progress_updates_sequence(self, service: TaskService, mock_repository):
        """Test sequence of progress updates."""
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

        # ACT - Update progress multiple times
        for progress in [10.0, 25.5, 50.0, 75.5, 100.0]:
            await service.update_progress("task_123", progress=progress)

        # ASSERT
        assert mock_repository.update_task.call_count == 5

    @pytest.mark.asyncio
    async def test_concurrent_task_operations(self, service: TaskService, mock_repository):
        """Test concurrent task operations."""
        # ARRANGE
        task1 = Task(
            id="task_1",
            type=TaskType.BACKTEST.value,
            name="Task 1",
            status=TaskStatus.PENDING.value,
            params={},
            created_by="test_user"
        )
        task2 = Task(
            id="task_2",
            type=TaskType.BACKTEST.value,
            name="Task 2",
            status=TaskStatus.RUNNING.value,
            params={},
            created_by="test_user"
        )

        # Setup mocks for concurrent operations
        async def get_task_by_id(task_id):
            if task_id == "task_1":
                return task1
            return task2

        mock_repository.get_task_by_id = AsyncMock(side_effect=get_task_by_id)
        mock_repository.update_task_status = AsyncMock(return_value=task1)
        mock_repository.update_task = AsyncMock(return_value=task2)

        # ACT - Run operations concurrently
        results = await asyncio.gather(
            service.start_task("task_1"),
            service.update_progress("task_2", progress=50.0)
        )

        # ASSERT
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_task_with_empty_string_parameters(self, service: TaskService, mock_repository):
        """Test task creation with empty string parameters."""
        # ARRANGE
        task_data = {
            "type": TaskType.BACKTEST.value,
            "name": "Test",
            "params": {"strategy_id": "", "dataset_id": ""},
            "created_by": "test_user"
        }
        expected_task = Task(id="task_123", status=TaskStatus.PENDING.value, **task_data)
        mock_repository.create_task = AsyncMock(return_value=expected_task)

        # ACT - Empty strings in required params should still be valid
        # (validation only checks for key presence, not value)
        task = await service.create_task(task_data)

        # ASSERT
        assert task.id == "task_123"

    @pytest.mark.asyncio
    async def test_task_repository_exception_handling(self, service: TaskService, mock_repository):
        """Test handling of repository exceptions."""
        # ARRANGE
        mock_repository.get_task_by_id = AsyncMock(side_effect=Exception("Database error"))

        # ACT & ASSERT
        with pytest.raises(Exception, match="Database error"):
            await service.get_task("task_123")

    @pytest.mark.asyncio
    async def test_task_constants_validation(self, service: TaskService):
        """Test that service constants are properly defined."""
        # ASSERT
        assert service.REQUIRED_FIELDS == {"type", "name", "params", "created_by"}
        assert TaskType.BACKTEST.value in service.TASK_PARAM_REQUIREMENTS
        assert TaskType.DATA_IMPORT.value in service.TASK_PARAM_REQUIREMENTS
        assert service.VALID_TRANSITIONS is not None

    @pytest.mark.asyncio
    async def test_get_next_pending_task_with_equal_priorities(self, service: TaskService, mock_repository):
        """Test getting next pending task when multiple tasks have equal priority."""
        # ARRANGE
        tasks = [
            Task(id="task_1", type=TaskType.BACKTEST.value, name="Task 1",
                 status=TaskStatus.PENDING.value, priority=TaskPriority.HIGH.value,
                 params={}, created_by="test_user"),
            Task(id="task_2", type=TaskType.BACKTEST.value, name="Task 2",
                 status=TaskStatus.PENDING.value, priority=TaskPriority.HIGH.value,
                 params={}, created_by="test_user"),
        ]
        mock_repository.get_pending_tasks_by_priority = AsyncMock(return_value=tasks)

        # ACT
        result = await service.get_next_pending_task()

        # ASSERT
        assert result is not None
        assert result.priority == TaskPriority.HIGH.value
