"""
Task Service

Handles task lifecycle management, validation, and queue operations.
Manages task status transitions and progress tracking.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from app.database.repositories.task_repository import TaskRepository
from app.database.models.task import Task, TaskType, TaskStatus, TaskPriority
from app.modules.task_scheduling.exceptions import (
    TaskNotFoundError,
    TaskValidationError,
    TaskExecutionError
)

logger = logging.getLogger(__name__)


class TaskService:
    """
    Service for handling task scheduling operations.

    Provides methods for:
    - Task creation and validation
    - Task lifecycle management (start, pause, resume, cancel, complete)
    - Task progress tracking
    - Task queue management
    - Task status transitions
    """

    # Required fields for task creation
    REQUIRED_FIELDS = {"type", "name", "params", "created_by"}

    # Task type specific parameter requirements
    TASK_PARAM_REQUIREMENTS = {
        TaskType.BACKTEST.value: {"strategy_id", "dataset_id"},
        TaskType.OPTIMIZATION.value: {"strategy_id", "dataset_id"},
        TaskType.DATA_IMPORT.value: {"file_path"},
        TaskType.DATA_PREPROCESSING.value: {"dataset_id"},
        TaskType.FACTOR_BACKTEST.value: {"factor_id", "dataset_id"},
        TaskType.CUSTOM_CODE.value: {"code"},
    }

    # Valid status transitions
    VALID_TRANSITIONS = {
        TaskStatus.PENDING.value: {TaskStatus.RUNNING.value, TaskStatus.CANCELLED.value},
        TaskStatus.RUNNING.value: {TaskStatus.PAUSED.value, TaskStatus.COMPLETED.value,
                                   TaskStatus.FAILED.value, TaskStatus.CANCELLED.value},
        TaskStatus.PAUSED.value: {TaskStatus.RUNNING.value, TaskStatus.CANCELLED.value},
    }

    def __init__(self, repository: TaskRepository):
        """
        Initialize TaskService.

        Args:
            repository: TaskRepository instance for data access
        """
        self.repository = repository

    async def create_task(self, task_data: Dict[str, Any]) -> Task:
        """
        Create a new task with validation.

        Args:
            task_data: Dictionary containing task fields

        Returns:
            Created Task instance

        Raises:
            TaskValidationError: If validation fails
        """
        # Validate required fields
        self._validate_required_fields(task_data)

        # Validate task type
        task_type = task_data.get("type")
        if task_type not in [t.value for t in TaskType]:
            raise TaskValidationError(f"Invalid task type: {task_type}")

        # Validate task parameters
        params = task_data.get("params", {})
        self.validate_task_params(task_type, params)

        # Set default values
        if "status" not in task_data:
            task_data["status"] = TaskStatus.PENDING.value
        if "priority" not in task_data:
            task_data["priority"] = TaskPriority.NORMAL.value
        if "progress" not in task_data:
            task_data["progress"] = 0.0

        # Create task
        task = await self.repository.create_task(task_data)

        logger.info(
            f"Created task {task.id}",
            extra={
                "task_id": task.id,
                "task_type": task.type,
                "created_by": task.created_by
            }
        )

        return task

    async def get_task(self, task_id: str) -> Task:
        """
        Get task by ID.

        Args:
            task_id: Task ID

        Returns:
            Task instance

        Raises:
            TaskNotFoundError: If task not found
        """
        task = await self.repository.get_task_by_id(task_id)
        if not task:
            raise TaskNotFoundError(f"Task not found: {task_id}")
        return task

    async def list_tasks(self, skip: int = 0, limit: int = 100) -> List[Task]:
        """
        List tasks with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of Task instances
        """
        return await self.repository.get_tasks(skip=skip, limit=limit)

    async def start_task(self, task_id: str) -> Task:
        """
        Start a pending task.

        Args:
            task_id: Task ID

        Returns:
            Updated Task instance

        Raises:
            TaskNotFoundError: If task not found
            TaskExecutionError: If task cannot be started
        """
        task = await self.get_task(task_id)

        # Validate status transition
        if task.status != TaskStatus.PENDING.value:
            raise TaskExecutionError(
                f"Cannot start task with status {task.status}. "
                f"Task must be in PENDING status."
            )

        # Update status to RUNNING
        updated_task = await self.repository.update_task_status(
            task_id,
            TaskStatus.RUNNING.value
        )

        # Update the task object's status for the return value
        updated_task.status = TaskStatus.RUNNING.value

        logger.info(f"Started task {task_id}")
        return updated_task

    async def pause_task(self, task_id: str) -> Task:
        """
        Pause a running task.

        Args:
            task_id: Task ID

        Returns:
            Updated Task instance

        Raises:
            TaskNotFoundError: If task not found
            TaskExecutionError: If task cannot be paused
        """
        task = await self.get_task(task_id)

        # Validate status transition
        if task.status != TaskStatus.RUNNING.value:
            raise TaskExecutionError(
                f"Cannot pause task with status {task.status}. "
                f"Task must be in RUNNING status."
            )

        # Update status to PAUSED
        updated_task = await self.repository.update_task_status(
            task_id,
            TaskStatus.PAUSED.value
        )

        # Update the task object's status for the return value
        updated_task.status = TaskStatus.PAUSED.value

        logger.info(f"Paused task {task_id}")
        return updated_task

    async def resume_task(self, task_id: str) -> Task:
        """
        Resume a paused task.

        Args:
            task_id: Task ID

        Returns:
            Updated Task instance

        Raises:
            TaskNotFoundError: If task not found
            TaskExecutionError: If task cannot be resumed
        """
        task = await self.get_task(task_id)

        # Validate status transition
        if task.status != TaskStatus.PAUSED.value:
            raise TaskExecutionError(
                f"Cannot resume task with status {task.status}. "
                f"Task must be in PAUSED status."
            )

        # Update status to RUNNING
        updated_task = await self.repository.update_task_status(
            task_id,
            TaskStatus.RUNNING.value
        )

        # Update the task object's status for the return value
        updated_task.status = TaskStatus.RUNNING.value

        logger.info(f"Resumed task {task_id}")
        return updated_task

    async def cancel_task(self, task_id: str) -> Task:
        """
        Cancel a task.

        Args:
            task_id: Task ID

        Returns:
            Updated Task instance

        Raises:
            TaskNotFoundError: If task not found
        """
        task = await self.get_task(task_id)

        # Can cancel tasks in PENDING, RUNNING, or PAUSED status
        if task.status in [TaskStatus.COMPLETED.value, TaskStatus.FAILED.value,
                          TaskStatus.CANCELLED.value]:
            raise TaskExecutionError(
                f"Cannot cancel task with status {task.status}. "
                f"Task is already in a terminal state."
            )

        # Update status to CANCELLED
        updated_task = await self.repository.update_task_status(
            task_id,
            TaskStatus.CANCELLED.value
        )

        # Update the task object's status for the return value
        updated_task.status = TaskStatus.CANCELLED.value

        logger.info(f"Cancelled task {task_id}")
        return updated_task

    async def complete_task(
        self,
        task_id: str,
        result_data: Optional[Dict[str, Any]] = None
    ) -> Task:
        """
        Complete task with result.

        Args:
            task_id: Task ID
            result_data: Task result data

        Returns:
            Updated Task instance

        Raises:
            TaskNotFoundError: If task not found
        """
        task = await self.get_task(task_id)

        # Update task with completion data
        update_data = {
            "status": TaskStatus.COMPLETED.value,
            "result": result_data or {},
            "progress": 100.0,
            "completed_at": datetime.utcnow()
        }

        updated_task = await self.repository.update_task(task_id, update_data)

        # Update the task object's attributes for the return value
        updated_task.status = TaskStatus.COMPLETED.value
        updated_task.result = result_data or {}
        updated_task.progress = 100.0

        logger.info(f"Completed task {task_id}")
        return updated_task

    async def fail_task(self, task_id: str, error_message: str) -> Task:
        """
        Mark task as failed with error message.

        Args:
            task_id: Task ID
            error_message: Error message

        Returns:
            Updated Task instance

        Raises:
            TaskNotFoundError: If task not found
        """
        task = await self.get_task(task_id)

        # Update task with failure data
        update_data = {
            "status": TaskStatus.FAILED.value,
            "error": error_message,
            "completed_at": datetime.utcnow()
        }

        updated_task = await self.repository.update_task(task_id, update_data)

        # Update the task object's attributes for the return value
        updated_task.status = TaskStatus.FAILED.value
        updated_task.error = error_message

        logger.error(f"Task {task_id} failed: {error_message}")
        return updated_task

    async def update_progress(
        self,
        task_id: str,
        progress: float,
        current_step: Optional[str] = None,
        eta: Optional[int] = None
    ) -> Task:
        """
        Update task progress.

        Args:
            task_id: Task ID
            progress: Progress percentage (0-100)
            current_step: Current step description
            eta: Estimated time remaining (seconds)

        Returns:
            Updated Task instance

        Raises:
            TaskNotFoundError: If task not found
        """
        task = await self.get_task(task_id)

        # Prepare update data
        update_data = {
            "progress": progress,
        }

        if current_step is not None:
            update_data["current_step"] = current_step

        if eta is not None:
            update_data["eta"] = eta

        updated_task = await self.repository.update_task(task_id, update_data)

        logger.debug(
            f"Updated task {task_id} progress: {progress}%",
            extra={
                "task_id": task_id,
                "progress": progress,
                "current_step": current_step
            }
        )

        return updated_task

    async def get_next_pending_task(self) -> Optional[Task]:
        """
        Get next pending task by priority.

        Returns:
            Highest priority pending task or None if no pending tasks
        """
        tasks = await self.repository.get_pending_tasks_by_priority()

        if not tasks:
            return None

        # Repository returns tasks sorted by priority (highest first)
        # Find the task with the highest priority
        highest_priority_task = tasks[0]
        for task in tasks[1:]:
            if task.priority > highest_priority_task.priority:
                highest_priority_task = task

        return highest_priority_task

    async def get_running_tasks_count(self) -> int:
        """
        Get count of running tasks.

        Returns:
            Count of running tasks
        """
        return await self.repository.count_tasks_by_status(TaskStatus.RUNNING.value)

    async def get_user_tasks(self, user_id: str) -> List[Task]:
        """
        Get tasks for a specific user.

        Args:
            user_id: User ID

        Returns:
            List of Task instances
        """
        return await self.repository.get_tasks_by_user(user_id)

    def validate_task_params(self, task_type: str, params: Dict[str, Any]) -> bool:
        """
        Validate task parameters based on task type.

        Args:
            task_type: Task type
            params: Task parameters

        Returns:
            True if valid

        Raises:
            TaskValidationError: If validation fails
        """
        # Check if task type has parameter requirements
        if task_type not in self.TASK_PARAM_REQUIREMENTS:
            # No specific requirements for this task type
            return True

        required_params = self.TASK_PARAM_REQUIREMENTS[task_type]

        # Check for missing required parameters
        missing_params = required_params - set(params.keys())
        if missing_params:
            raise TaskValidationError(
                f"Missing required parameter(s) for {task_type}: "
                f"{', '.join(missing_params)}"
            )

        return True

    async def delete_task(self, task_id: str) -> bool:
        """
        Delete a task.

        Args:
            task_id: Task ID

        Returns:
            True if deleted

        Raises:
            TaskNotFoundError: If task not found
            TaskExecutionError: If task is running
        """
        task = await self.get_task(task_id)

        # Cannot delete running tasks
        if task.status == TaskStatus.RUNNING.value:
            raise TaskExecutionError(
                f"Cannot delete running task {task_id}. "
                f"Please pause or cancel the task first."
            )

        # Delete task
        result = await self.repository.delete_task(task_id)

        if result:
            logger.info(f"Deleted task {task_id}")

        return result

    def _validate_required_fields(self, task_data: Dict[str, Any]) -> None:
        """
        Validate required fields are present.

        Args:
            task_data: Task data dictionary

        Raises:
            TaskValidationError: If required fields are missing
        """
        missing_fields = self.REQUIRED_FIELDS - set(task_data.keys())
        if missing_fields:
            raise TaskValidationError(
                f"Missing required field(s): {', '.join(missing_fields)}"
            )
