"""
Import Task Repository

Data access layer for ImportTask model with async SQLAlchemy operations.
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.base import BaseRepository
from app.database.models.import_task import ImportTask, ImportStatus, ImportType


class ImportTaskRepository(BaseRepository[ImportTask]):
    """Repository for ImportTask model with specialized query methods"""

    def __init__(self, session: AsyncSession):
        super().__init__(ImportTask, session)

    async def get_by_user(
        self,
        user_id: str,
        status: Optional[ImportStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ImportTask]:
        """
        Get import tasks by user ID with optional status filter

        Args:
            user_id: User ID
            status: Optional status filter
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of import tasks
        """
        query = select(self.model).where(
            self.model.user_id == user_id,
            self.model.is_deleted == False
        )

        if status:
            query = query.where(self.model.status == status.value)

        query = query.order_by(self.model.created_at.desc()).offset(skip).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_active_tasks(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[ImportTask]:
        """
        Get all active (not completed/failed/cancelled) import tasks

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of active import tasks
        """
        active_statuses = [
            ImportStatus.PENDING.value,
            ImportStatus.VALIDATING.value,
            ImportStatus.PARSING.value,
            ImportStatus.PROCESSING.value,
        ]

        query = select(self.model).where(
            self.model.status.in_(active_statuses),
            self.model.is_deleted == False
        ).order_by(self.model.created_at.desc()).offset(skip).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_status(
        self,
        status: ImportStatus,
        skip: int = 0,
        limit: int = 100
    ) -> List[ImportTask]:
        """
        Get import tasks by status

        Args:
            status: Import status
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of import tasks with specified status
        """
        query = select(self.model).where(
            self.model.status == status.value,
            self.model.is_deleted == False
        ).order_by(self.model.created_at.desc()).offset(skip).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_dataset(
        self,
        dataset_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[ImportTask]:
        """
        Get import tasks that created/updated a specific dataset

        Args:
            dataset_id: Dataset ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of import tasks for the dataset
        """
        query = select(self.model).where(
            self.model.dataset_id == dataset_id,
            self.model.is_deleted == False
        ).order_by(self.model.created_at.desc()).offset(skip).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_by_status(self, status: ImportStatus) -> int:
        """
        Count import tasks by status

        Args:
            status: Import status

        Returns:
            Count of tasks with specified status
        """
        return await self.count(status=status.value)
