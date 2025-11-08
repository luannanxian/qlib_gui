"""
Task Scheduling API Endpoints

Handles task lifecycle management operations including:
- Task creation and retrieval
- Task status transitions (start, pause, resume, cancel)
- Progress tracking
- Task deletion
- User task queries
- Task statistics
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.database.repositories.task_repository import TaskRepository
from app.database.models.task import TaskStatus
from app.modules.task_scheduling.services.task_service import TaskService
from app.modules.task_scheduling.schemas import (
    TaskCreate,
    TaskResponse,
    TaskProgressUpdate,
    TaskListResponse,
    TaskStats
)
from app.modules.task_scheduling.exceptions import (
    TaskNotFoundError,
    TaskValidationError,
    TaskExecutionError
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


# Dependency to get TaskService
async def get_task_service(session: AsyncSession = Depends(get_db)) -> TaskService:
    """
    Get TaskService instance with repository.

    Args:
        session: Database session from dependency injection

    Returns:
        TaskService instance
    """
    repository = TaskRepository(session)
    return TaskService(repository)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=TaskResponse,
    summary="Create new task",
    description="Create a new task with validation of type and parameters"
)
async def create_task(
    task_data: TaskCreate,
    service: TaskService = Depends(get_task_service)
) -> TaskResponse:
    """
    Create a new task.

    Args:
        task_data: Task creation data
        service: TaskService instance

    Returns:
        Created task

    Raises:
        HTTPException: 400 if validation fails, 422 if request is malformed
    """
    try:
        # Convert Pydantic model to dict
        task_dict = task_data.model_dump()

        # Create task
        task = await service.create_task(task_dict)

        logger.info(f"Created task {task.id} of type {task.type}")

        return TaskResponse.model_validate(task)

    except TaskValidationError as e:
        logger.warning(f"Task validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/stats",
    response_model=TaskStats,
    summary="Get task statistics",
    description="Get statistics about tasks grouped by status"
)
async def get_task_stats(
    service: TaskService = Depends(get_task_service)
) -> TaskStats:
    """
    Get task statistics.

    Args:
        service: TaskService instance

    Returns:
        Task statistics by status
    """
    # Get counts for each status
    repository = service.repository

    pending_count = await repository.count_tasks_by_status(TaskStatus.PENDING.value)
    running_count = await repository.count_tasks_by_status(TaskStatus.RUNNING.value)
    paused_count = await repository.count_tasks_by_status(TaskStatus.PAUSED.value)
    completed_count = await repository.count_tasks_by_status(TaskStatus.COMPLETED.value)
    failed_count = await repository.count_tasks_by_status(TaskStatus.FAILED.value)
    cancelled_count = await repository.count_tasks_by_status(TaskStatus.CANCELLED.value)

    total_count = (
        pending_count + running_count + paused_count +
        completed_count + failed_count + cancelled_count
    )

    return TaskStats(
        total=total_count,
        pending=pending_count,
        running=running_count,
        paused=paused_count,
        completed=completed_count,
        failed=failed_count,
        cancelled=cancelled_count
    )


@router.get(
    "/pending/next",
    response_model=TaskResponse,
    summary="Get next pending task",
    description="Get the next pending task by priority (highest priority first)"
)
async def get_next_pending_task(
    service: TaskService = Depends(get_task_service)
) -> TaskResponse:
    """
    Get next pending task by priority.

    Args:
        service: TaskService instance

    Returns:
        Highest priority pending task

    Raises:
        HTTPException: 404 if no pending tasks available
    """
    task = await service.get_next_pending_task()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No pending tasks available"
        )

    return TaskResponse.model_validate(task)


@router.get(
    "/user/{user_id}",
    response_model=List[TaskResponse],
    summary="Get user's tasks",
    description="Retrieve all tasks created by a specific user"
)
async def get_user_tasks(
    user_id: str,
    service: TaskService = Depends(get_task_service)
) -> List[TaskResponse]:
    """
    Get tasks for a specific user.

    Args:
        user_id: User ID
        service: TaskService instance

    Returns:
        List of user's tasks
    """
    tasks = await service.get_user_tasks(user_id)

    return [TaskResponse.model_validate(task) for task in tasks]


@router.get(
    "",
    response_model=TaskListResponse,
    summary="List tasks with pagination",
    description="Retrieve a paginated list of tasks ordered by creation time (newest first)"
)
async def list_tasks(
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum number of records to return"),
    service: TaskService = Depends(get_task_service)
) -> TaskListResponse:
    """
    List tasks with pagination.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        service: TaskService instance

    Returns:
        Paginated list of tasks
    """
    # Get tasks
    tasks = await service.list_tasks(skip=skip, limit=limit)

    # Get total count from repository
    repository = service.repository
    from app.database.models.task import TaskStatus

    # Count all non-deleted tasks
    total = 0
    for status in TaskStatus:
        total += await repository.count_tasks_by_status(status.value)

    # Convert to response models
    task_responses = [TaskResponse.model_validate(task) for task in tasks]

    return TaskListResponse(
        total=total,
        items=task_responses,
        skip=skip,
        limit=limit
    )


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get task by ID",
    description="Retrieve a specific task by its ID"
)
async def get_task(
    task_id: str,
    service: TaskService = Depends(get_task_service)
) -> TaskResponse:
    """
    Get task by ID.

    Args:
        task_id: Task ID
        service: TaskService instance

    Returns:
        Task details

    Raises:
        HTTPException: 404 if task not found
    """
    try:
        task = await service.get_task(task_id)
        return TaskResponse.model_validate(task)

    except TaskNotFoundError as e:
        logger.warning(f"Task not found: {task_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put(
    "/{task_id}/start",
    response_model=TaskResponse,
    summary="Start task",
    description="Start a pending task, transitioning it to RUNNING status"
)
async def start_task(
    task_id: str,
    service: TaskService = Depends(get_task_service)
) -> TaskResponse:
    """
    Start a pending task.

    Args:
        task_id: Task ID
        service: TaskService instance

    Returns:
        Updated task

    Raises:
        HTTPException: 404 if task not found, 400 if task cannot be started
    """
    try:
        task = await service.start_task(task_id)
        logger.info(f"Started task {task_id}")
        return TaskResponse.model_validate(task)

    except TaskNotFoundError as e:
        logger.warning(f"Task not found: {task_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except TaskExecutionError as e:
        logger.warning(f"Cannot start task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put(
    "/{task_id}/pause",
    response_model=TaskResponse,
    summary="Pause task",
    description="Pause a running task, transitioning it to PAUSED status"
)
async def pause_task(
    task_id: str,
    service: TaskService = Depends(get_task_service)
) -> TaskResponse:
    """
    Pause a running task.

    Args:
        task_id: Task ID
        service: TaskService instance

    Returns:
        Updated task

    Raises:
        HTTPException: 404 if task not found, 400 if task cannot be paused
    """
    try:
        task = await service.pause_task(task_id)
        logger.info(f"Paused task {task_id}")
        return TaskResponse.model_validate(task)

    except TaskNotFoundError as e:
        logger.warning(f"Task not found: {task_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except TaskExecutionError as e:
        logger.warning(f"Cannot pause task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put(
    "/{task_id}/resume",
    response_model=TaskResponse,
    summary="Resume task",
    description="Resume a paused task, transitioning it back to RUNNING status"
)
async def resume_task(
    task_id: str,
    service: TaskService = Depends(get_task_service)
) -> TaskResponse:
    """
    Resume a paused task.

    Args:
        task_id: Task ID
        service: TaskService instance

    Returns:
        Updated task

    Raises:
        HTTPException: 404 if task not found, 400 if task cannot be resumed
    """
    try:
        task = await service.resume_task(task_id)
        logger.info(f"Resumed task {task_id}")
        return TaskResponse.model_validate(task)

    except TaskNotFoundError as e:
        logger.warning(f"Task not found: {task_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except TaskExecutionError as e:
        logger.warning(f"Cannot resume task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put(
    "/{task_id}/cancel",
    response_model=TaskResponse,
    summary="Cancel task",
    description="Cancel a task in PENDING, RUNNING, or PAUSED status"
)
async def cancel_task(
    task_id: str,
    service: TaskService = Depends(get_task_service)
) -> TaskResponse:
    """
    Cancel a task.

    Args:
        task_id: Task ID
        service: TaskService instance

    Returns:
        Updated task

    Raises:
        HTTPException: 404 if task not found, 400 if task cannot be cancelled
    """
    try:
        task = await service.cancel_task(task_id)
        logger.info(f"Cancelled task {task_id}")
        return TaskResponse.model_validate(task)

    except TaskNotFoundError as e:
        logger.warning(f"Task not found: {task_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except TaskExecutionError as e:
        logger.warning(f"Cannot cancel task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put(
    "/{task_id}/progress",
    response_model=TaskResponse,
    summary="Update task progress",
    description="Update the progress, current step, and ETA of a task"
)
async def update_progress(
    task_id: str,
    progress_data: TaskProgressUpdate,
    service: TaskService = Depends(get_task_service)
) -> TaskResponse:
    """
    Update task progress.

    Args:
        task_id: Task ID
        progress_data: Progress update data
        service: TaskService instance

    Returns:
        Updated task

    Raises:
        HTTPException: 404 if task not found
    """
    try:
        task = await service.update_progress(
            task_id=task_id,
            progress=progress_data.progress,
            current_step=progress_data.current_step,
            eta=progress_data.eta
        )

        logger.debug(f"Updated progress for task {task_id}: {progress_data.progress}%")

        return TaskResponse.model_validate(task)

    except TaskNotFoundError as e:
        logger.warning(f"Task not found: {task_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete(
    "/{task_id}",
    summary="Delete task",
    description="Soft delete a task (cannot delete running tasks)"
)
async def delete_task(
    task_id: str,
    service: TaskService = Depends(get_task_service)
):
    """
    Delete a task.

    Args:
        task_id: Task ID
        service: TaskService instance

    Returns:
        Success message

    Raises:
        HTTPException: 404 if task not found, 400 if task is running
    """
    try:
        await service.delete_task(task_id)
        logger.info(f"Deleted task {task_id}")

        return {"message": "Task deleted successfully"}

    except TaskNotFoundError as e:
        logger.warning(f"Task not found: {task_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except TaskExecutionError as e:
        logger.warning(f"Cannot delete task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


