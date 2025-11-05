"""
Indicator Repository

Repository for managing technical indicator components with specialized
query methods for category filtering, search, and usage tracking.
"""

from typing import List, Optional

from loguru import logger
from sqlalchemy import select, or_, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.indicator import IndicatorComponent, IndicatorCategory, IndicatorSource
from app.database.repositories.base import BaseRepository


class IndicatorRepository(BaseRepository[IndicatorComponent]):
    """
    Repository for IndicatorComponent operations.

    Provides specialized methods for:
    - Category-based filtering
    - Multi-language name search
    - Popular indicators ranking
    - System vs user indicators
    - Atomic usage count increment
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with IndicatorComponent model"""
        super().__init__(IndicatorComponent, session)

    async def get_by_category(
        self,
        category: IndicatorCategory,
        skip: int = 0,
        limit: int = 100,
        enabled_only: bool = True
    ) -> List[IndicatorComponent]:
        """
        Get indicators by category.

        Args:
            category: Indicator category
            skip: Number of records to skip
            limit: Maximum number of records to return
            enabled_only: Filter only enabled indicators

        Returns:
            List of indicators in the category
        """
        stmt = select(IndicatorComponent).where(
            IndicatorComponent.category == category.value,
            IndicatorComponent.is_deleted == False
        )

        if enabled_only:
            stmt = stmt.where(IndicatorComponent.is_enabled == True)

        stmt = stmt.order_by(IndicatorComponent.usage_count.desc())
        stmt = stmt.offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        indicators = list(result.scalars().all())

        logger.debug(f"Found {len(indicators)} indicators in category {category.value}")
        return indicators

    async def search_by_name(
        self,
        keyword: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[IndicatorComponent]:
        """
        Search indicators by name (Chinese, English) or code.

        Args:
            keyword: Search keyword
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of matching indicators
        """
        # Use LIKE for fuzzy search (works in SQLite and MySQL)
        search_pattern = f"%{keyword}%"

        stmt = select(IndicatorComponent).where(
            IndicatorComponent.is_deleted == False,
            or_(
                IndicatorComponent.name_zh.like(search_pattern),
                IndicatorComponent.name_en.like(search_pattern),
                IndicatorComponent.code.like(search_pattern)
            )
        )

        stmt = stmt.order_by(IndicatorComponent.usage_count.desc())
        stmt = stmt.offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        indicators = list(result.scalars().all())

        logger.debug(f"Search '{keyword}' found {len(indicators)} indicators")
        return indicators

    async def get_popular_indicators(
        self,
        limit: int = 10,
        category: Optional[IndicatorCategory] = None
    ) -> List[IndicatorComponent]:
        """
        Get popular indicators sorted by usage count.

        Args:
            limit: Maximum number of indicators to return
            category: Optional category filter

        Returns:
            List of popular indicators
        """
        stmt = select(IndicatorComponent).where(
            IndicatorComponent.is_deleted == False,
            IndicatorComponent.is_enabled == True
        )

        if category:
            stmt = stmt.where(IndicatorComponent.category == category.value)

        stmt = stmt.order_by(IndicatorComponent.usage_count.desc())
        stmt = stmt.limit(limit)

        result = await self.session.execute(stmt)
        indicators = list(result.scalars().all())

        logger.debug(f"Retrieved {len(indicators)} popular indicators")
        return indicators

    async def get_system_indicators(
        self,
        skip: int = 0,
        limit: int = 100,
        enabled_only: bool = True
    ) -> List[IndicatorComponent]:
        """
        Get system built-in indicators.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            enabled_only: Filter only enabled indicators

        Returns:
            List of system indicators
        """
        stmt = select(IndicatorComponent).where(
            IndicatorComponent.is_deleted == False,
            IndicatorComponent.is_system == True
        )

        if enabled_only:
            stmt = stmt.where(IndicatorComponent.is_enabled == True)

        stmt = stmt.order_by(IndicatorComponent.code)
        stmt = stmt.offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        indicators = list(result.scalars().all())

        logger.debug(f"Retrieved {len(indicators)} system indicators")
        return indicators

    async def get_user_indicators(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[IndicatorComponent]:
        """
        Get user-defined indicators.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of user indicators
        """
        stmt = select(IndicatorComponent).where(
            IndicatorComponent.is_deleted == False,
            IndicatorComponent.is_system == False
        )

        stmt = stmt.order_by(IndicatorComponent.created_at.desc())
        stmt = stmt.offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        indicators = list(result.scalars().all())

        logger.debug(f"Retrieved {len(indicators)} user indicators")
        return indicators

    async def increment_usage_count(
        self,
        indicator_id: str,
        commit: bool = True
    ) -> Optional[IndicatorComponent]:
        """
        Atomically increment usage count for an indicator.

        Args:
            indicator_id: Indicator ID
            commit: Whether to commit the transaction

        Returns:
            Updated indicator or None if not found
        """
        # First check if indicator exists
        indicator = await self.get(indicator_id)
        if not indicator:
            logger.warning(f"Indicator not found: {indicator_id}")
            return None

        # Use atomic update to avoid race conditions
        stmt = (
            update(IndicatorComponent)
            .where(IndicatorComponent.id == indicator_id)
            .values(usage_count=IndicatorComponent.usage_count + 1)
        )

        await self.session.execute(stmt)

        if commit:
            await self.session.commit()

        # Refresh to get updated value
        await self.session.refresh(indicator)

        logger.debug(f"Incremented usage count for indicator {indicator_id} to {indicator.usage_count}")
        return indicator
