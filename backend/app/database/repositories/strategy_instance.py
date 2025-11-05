"""
StrategyInstance Repository

Handles database operations for strategy instances including:
- CRUD operations
- User-specific queries
- Template-based queries
- Version history management
- Status filtering
"""

from typing import List, Optional
from sqlalchemy import select, and_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.strategy import StrategyInstance, StrategyStatus
from app.database.repositories.base import BaseRepository


class StrategyInstanceRepository(BaseRepository[StrategyInstance]):
    """Repository for StrategyInstance model operations"""

    def __init__(self, db: AsyncSession):
        super().__init__(StrategyInstance, db)

    async def get_by_user(
        self,
        user_id: str,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[StrategyInstance]:
        """
        Get all strategy instances for a user

        Args:
            user_id: User ID
            status: Optional status filter
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of strategy instances
        """
        filters = [
            StrategyInstance.user_id == user_id,
            StrategyInstance.is_deleted == False
        ]

        if status:
            filters.append(StrategyInstance.status == status)

        query = (
            select(StrategyInstance)
            .where(and_(*filters))
            .order_by(desc(StrategyInstance.created_at))
            .offset(skip)
            .limit(limit)
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_template(
        self,
        template_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[StrategyInstance]:
        """
        Get all instances created from a template

        Args:
            template_id: Template ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of strategy instances
        """
        query = (
            select(StrategyInstance)
            .where(
                and_(
                    StrategyInstance.template_id == template_id,
                    StrategyInstance.is_deleted == False
                )
            )
            .order_by(desc(StrategyInstance.created_at))
            .offset(skip)
            .limit(limit)
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_versions(self, parent_id: str) -> List[StrategyInstance]:
        """
        Get version history for a strategy instance

        Args:
            parent_id: Parent instance ID

        Returns:
            List of version snapshots sorted by version descending
        """
        query = (
            select(StrategyInstance)
            .where(
                and_(
                    StrategyInstance.parent_version_id == parent_id,
                    StrategyInstance.is_deleted == False
                )
            )
            .order_by(desc(StrategyInstance.version))
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_latest_version(self, parent_id: str) -> Optional[StrategyInstance]:
        """
        Get the latest version snapshot for a strategy

        Args:
            parent_id: Parent instance ID

        Returns:
            Latest version snapshot or None
        """
        query = (
            select(StrategyInstance)
            .where(
                and_(
                    StrategyInstance.parent_version_id == parent_id,
                    StrategyInstance.is_deleted == False
                )
            )
            .order_by(desc(StrategyInstance.version))
            .limit(1)
        )

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def count_versions(self, parent_id: str) -> int:
        """
        Count version snapshots for a strategy

        Args:
            parent_id: Parent instance ID

        Returns:
            Number of version snapshots
        """
        query = (
            select(func.count())
            .select_from(StrategyInstance)
            .where(
                and_(
                    StrategyInstance.parent_version_id == parent_id,
                    StrategyInstance.is_deleted == False
                )
            )
        )

        result = await self.session.execute(query)
        return result.scalar_one()

    async def get_active_strategies(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[StrategyInstance]:
        """
        Get all active strategy instances

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of active strategy instances
        """
        query = (
            select(StrategyInstance)
            .where(
                and_(
                    StrategyInstance.status == StrategyStatus.ACTIVE.value,
                    StrategyInstance.is_deleted == False
                )
            )
            .order_by(desc(StrategyInstance.created_at))
            .offset(skip)
            .limit(limit)
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_by_user(
        self,
        user_id: str,
        status: Optional[str] = None,
        template_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[StrategyInstance]:
        """
        List strategy instances for a user with filters

        Args:
            user_id: User ID
            status: Optional status filter
            template_id: Optional template ID filter
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of strategy instances
        """
        filters = [
            StrategyInstance.user_id == user_id,
            StrategyInstance.is_deleted == False,
            StrategyInstance.parent_version_id.is_(None)  # Only main instances, not versions
        ]

        if status:
            filters.append(StrategyInstance.status == status)

        if template_id:
            filters.append(StrategyInstance.template_id == template_id)

        query = (
            select(StrategyInstance)
            .where(and_(*filters))
            .order_by(desc(StrategyInstance.created_at))
            .offset(skip)
            .limit(limit)
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_by_user(
        self,
        user_id: str,
        status: Optional[str] = None,
        template_id: Optional[str] = None
    ) -> int:
        """
        Count strategy instances for a user with filters

        Args:
            user_id: User ID
            status: Optional status filter
            template_id: Optional template ID filter

        Returns:
            Total count of matching instances
        """
        filters = [
            StrategyInstance.user_id == user_id,
            StrategyInstance.is_deleted == False,
            StrategyInstance.parent_version_id.is_(None)  # Only main instances, not versions
        ]

        if status:
            filters.append(StrategyInstance.status == status)

        if template_id:
            filters.append(StrategyInstance.template_id == template_id)

        query = (
            select(func.count())
            .select_from(StrategyInstance)
            .where(and_(*filters))
        )

        result = await self.session.execute(query)
        return result.scalar() or 0

