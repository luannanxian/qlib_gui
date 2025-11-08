"""
Task Repository

This module provides data access layer for task scheduling operations.
Handles CRUD operations for Task models.

Features:
- Create, read, update, delete operations
- Query by status, type, priority, user
- Soft delete support
- Pagination support
- Task counting and filtering
"""

from typing import List, Optional, Dict, Any
import logging

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.database.models.task import Task, TaskStatus
from app.modules.task_scheduling.exceptions import TaskSchedulingError

logger = logging.getLogger(__name__)


class TaskRepository:
    """Repository for task operations"""

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: Async SQLAlchemy session
        """
        self.session = session

    # ==================== Task CRUD Operations ====================

    async def create_task(self, task_data: Dict[str, Any]) -> Task:
        """
        Create a new task.

        Args:
            task_data: Dictionary containing task fields

        Returns:
            Created Task instance

        Raises:
            TaskSchedulingError: If database operation fails
        """
        try:
            task = Task(**task_data)
            self.session.add(task)
            await self.session.commit()
            await self.session.refresh(task)
            logger.info(f"Created task: {task.id}")
            return task
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Failed to create task: {str(e)}", exc_info=True)
            raise TaskSchedulingError(f"Failed to create task: {str(e)}") from e

    async def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """
        Retrieve a task by ID.

        Args:
            task_id: Task ID

        Returns:
            Task instance or None if not found
        """
        stmt = select(Task).where(
            and_(
                Task.id == task_id,
                Task.is_deleted == False
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_tasks(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[Task]:
        """
        Retrieve tasks with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of Task instances
        """
        stmt = select(Task).where(
            Task.is_deleted == False
        ).order_by(
            Task.created_at.desc()
        ).offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_tasks_by_status(self, status: str) -> List[Task]:
        """
        Retrieve all tasks with a specific status.

        Args:
            status: Task status (PENDING, RUNNING, COMPLETED, FAILED, CANCELLED)

        Returns:
            List of Task instances
        """
        stmt = select(Task).where(
            and_(
                Task.status == status,
                Task.is_deleted == False
            )
        ).order_by(Task.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_tasks_by_type(self, task_type: str) -> List[Task]:
        """
        Retrieve all tasks of a specific type.

        Args:
            task_type: Task type (BACKTEST, DATA_IMPORT, etc.)

        Returns:
            List of Task instances
        """
        stmt = select(Task).where(
            and_(
                Task.type == task_type,
                Task.is_deleted == False
            )
        ).order_by(Task.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_tasks_by_user(self, user_id: str) -> List[Task]:
        """
        Retrieve all tasks created by a specific user.

        Args:
            user_id: User ID

        Returns:
            List of Task instances
        """
        stmt = select(Task).where(
            and_(
                Task.created_by == user_id,
                Task.is_deleted == False
            )
        ).order_by(Task.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_pending_tasks_by_priority(self) -> List[Task]:
        """
        Retrieve all pending tasks ordered by priority (highest first).

        Returns:
            List of Task instances ordered by priority descending
        """
        stmt = select(Task).where(
            and_(
                Task.status == TaskStatus.PENDING.value,
                Task.is_deleted == False
            )
        ).order_by(Task.priority.desc(), Task.created_at.asc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_running_tasks(self) -> List[Task]:
        """
        Retrieve all currently running tasks.

        Returns:
            List of Task instances with RUNNING status
        """
        return await self.get_tasks_by_status(TaskStatus.RUNNING.value)

    async def update_task_status(
        self,
        task_id: str,
        status: str
    ) -> Optional[Task]:
        """
        Update the status of a task.

        Args:
            task_id: Task ID
            status: New status value

        Returns:
            Updated Task instance or None if not found

        Raises:
            TaskSchedulingError: If database operation fails
        """
        try:
            task = await self.get_task_by_id(task_id)
            if not task:
                return None

            task.status = status
            await self.session.commit()
            await self.session.refresh(task)
            logger.info(f"Updated task status: {task_id} -> {status}")
            return task
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Failed to update task status {task_id}: {str(e)}", exc_info=True)
            raise TaskSchedulingError(f"Failed to update task status: {str(e)}") from e

    async def update_task(
        self,
        task_id: str,
        update_data: Dict[str, Any]
    ) -> Optional[Task]:
        """
        Update a task.

        Args:
            task_id: Task ID
            update_data: Dictionary containing fields to update

        Returns:
            Updated Task instance or None if not found

        Raises:
            TaskSchedulingError: If database operation fails
        """
        try:
            task = await self.get_task_by_id(task_id)
            if not task:
                return None

            for key, value in update_data.items():
                if hasattr(task, key):
                    setattr(task, key, value)

            await self.session.commit()
            await self.session.refresh(task)
            logger.info(f"Updated task: {task_id}")
            return task
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Failed to update task {task_id}: {str(e)}", exc_info=True)
            raise TaskSchedulingError(f"Failed to update task: {str(e)}") from e

    async def delete_task(self, task_id: str) -> bool:
        """
        Soft delete a task.

        Args:
            task_id: Task ID

        Returns:
            True if deleted, False if not found

        Raises:
            TaskSchedulingError: If database operation fails
        """
        try:
            task = await self.get_task_by_id(task_id)
            if not task:
                return False

            task.is_deleted = True
            await self.session.commit()
            logger.info(f"Deleted task: {task_id}")
            return True
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Failed to delete task {task_id}: {str(e)}", exc_info=True)
            raise TaskSchedulingError(f"Failed to delete task: {str(e)}") from e

    # ==================== Query Operations ====================

    async def count_tasks_by_status(self, status: str) -> int:
        """
        Count the number of tasks with a specific status.

        Args:
            status: Task status

        Returns:
            Count of tasks with the given status
        """
        stmt = select(func.count(Task.id)).where(
            and_(
                Task.status == status,
                Task.is_deleted == False
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0
