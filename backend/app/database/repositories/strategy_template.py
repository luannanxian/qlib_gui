"""
StrategyTemplateRepository

Repository pattern for StrategyTemplate model with specialized methods for:
- Popular templates (sorted by usage_count)
- Rating statistics management
- Search functionality
- Template usage tracking
"""

from typing import List, Optional

from loguru import logger
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.strategy import StrategyTemplate
from app.database.repositories.base import BaseRepository


class StrategyTemplateRepository(BaseRepository[StrategyTemplate]):
    """
    Repository for StrategyTemplate model.

    Extends BaseRepository with template-specific operations:
    - Get popular templates sorted by usage_count
    - Update rating statistics
    - Increment usage count
    - Search templates by name
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with StrategyTemplate model"""
        super().__init__(StrategyTemplate, session)

    async def get_popular(
        self,
        limit: int = 5,
        category: Optional[str] = None,
        include_deleted: bool = False
    ) -> List[StrategyTemplate]:
        """
        Get popular templates sorted by usage_count in descending order.

        Args:
            limit: Maximum number of templates to return
            category: Optional category filter
            include_deleted: Whether to include soft-deleted records

        Returns:
            List of popular templates

        Example:
            popular = await repo.get_popular(limit=5, category="TREND_FOLLOWING")
        """
        stmt = select(self.model)

        # Apply soft delete filter
        if not include_deleted:
            stmt = stmt.where(self.model.is_deleted == False)

        # Apply category filter
        if category:
            stmt = stmt.where(self.model.category == category)

        # Sort by usage_count descending, then by created_at descending
        stmt = stmt.order_by(
            self.model.usage_count.desc(),
            self.model.created_at.desc()
        ).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def increment_usage_count(self, id: str) -> Optional[StrategyTemplate]:
        """
        Increment the usage count for a template.

        Args:
            id: Template ID

        Returns:
            Updated template or None if not found

        Example:
            template = await repo.increment_usage_count("template-id")
        """
        template = await self.get(id)
        if template is None:
            logger.warning(f"StrategyTemplate not found: id={id}")
            return None

        template.usage_count += 1
        await self.session.flush()
        await self.session.refresh(template)

        logger.debug(f"Incremented usage_count for template id={id} to {template.usage_count}")
        return template

    async def update_rating_stats(
        self,
        id: str,
        rating_average: float,
        rating_count: int
    ) -> Optional[StrategyTemplate]:
        """
        Update rating statistics for a template.

        Args:
            id: Template ID
            rating_average: New average rating (0-5)
            rating_count: Total number of ratings

        Returns:
            Updated template or None if not found

        Example:
            template = await repo.update_rating_stats("id", 4.5, 10)
        """
        template = await self.get(id)
        if template is None:
            logger.warning(f"StrategyTemplate not found: id={id}")
            return None

        template.rating_average = rating_average
        template.rating_count = rating_count

        await self.session.flush()
        await self.session.refresh(template)

        logger.debug(
            f"Updated rating stats for template id={id}: "
            f"avg={rating_average}, count={rating_count}"
        )
        return template

    async def search(
        self,
        query: str,
        category: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False
    ) -> List[StrategyTemplate]:
        """
        Search templates by name (case-insensitive).

        Args:
            query: Search query string
            category: Optional category filter
            skip: Number of records to skip
            limit: Maximum number of records to return
            include_deleted: Whether to include soft-deleted records

        Returns:
            List of matching templates

        Example:
            results = await repo.search(
                query="MA",
                category="TREND_FOLLOWING",
                limit=10
            )
        """
        stmt = select(self.model)

        # Apply soft delete filter
        if not include_deleted:
            stmt = stmt.where(self.model.is_deleted == False)

        # Apply search query (case-insensitive)
        if query:
            search_pattern = f"%{query}%"
            stmt = stmt.where(
                or_(
                    self.model.name.ilike(search_pattern),
                    self.model.description.ilike(search_pattern)
                )
            )

        # Apply category filter
        if category:
            stmt = stmt.where(self.model.category == category)

        # Order by relevance (name matches first) and created_at
        stmt = stmt.order_by(self.model.created_at.desc())

        # Apply pagination
        stmt = stmt.offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_all(
        self,
        category: Optional[str] = None,
        is_system_template: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False
    ) -> List[StrategyTemplate]:
        """
        List all templates with optional filtering.

        Args:
            category: Optional category filter
            is_system_template: Optional system template filter
            skip: Number of records to skip
            limit: Maximum number of records to return
            include_deleted: Whether to include soft-deleted records

        Returns:
            List of templates

        Example:
            templates = await repo.list_all(
                category="TREND_FOLLOWING",
                is_system_template=True,
                limit=20
            )
        """
        stmt = select(self.model)

        # Apply soft delete filter
        if not include_deleted:
            stmt = stmt.where(self.model.is_deleted == False)

        # Apply category filter
        if category:
            stmt = stmt.where(self.model.category == category)

        # Apply system template filter
        if is_system_template is not None:
            stmt = stmt.where(self.model.is_system_template == is_system_template)

        # Order by created_at descending
        stmt = stmt.order_by(self.model.created_at.desc())

        # Apply pagination
        stmt = stmt.offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count(
        self,
        category: Optional[str] = None,
        is_system_template: Optional[bool] = None,
        include_deleted: bool = False
    ) -> int:
        """
        Count templates with optional filtering.

        Args:
            category: Optional category filter
            is_system_template: Optional system template filter
            include_deleted: Whether to include soft-deleted records

        Returns:
            Total count of matching templates

        Example:
            count = await repo.count(category="TREND_FOLLOWING")
        """
        stmt = select(func.count()).select_from(self.model)

        # Apply soft delete filter
        if not include_deleted:
            stmt = stmt.where(self.model.is_deleted == False)

        # Apply category filter
        if category:
            stmt = stmt.where(self.model.category == category)

        # Apply system template filter
        if is_system_template is not None:
            stmt = stmt.where(self.model.is_system_template == is_system_template)

        result = await self.session.execute(stmt)
        return result.scalar() or 0

