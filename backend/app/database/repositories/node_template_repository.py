"""
NodeTemplate Repository

Repository for managing node template operations with specialized
query methods for builder functionality.
"""

from typing import List, Optional

from loguru import logger
from sqlalchemy import select, or_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.strategy_builder import NodeTemplate, NodeTypeCategory
from app.database.repositories.base import BaseRepository


class NodeTemplateRepository(BaseRepository[NodeTemplate]):
    """
    Repository for NodeTemplate operations.

    Provides specialized methods for:
    - Type-based filtering (INDICATOR, SIGNAL, CONDITION, etc.)
    - User custom template management
    - Template search with multiple filters
    - Atomic usage count increment
    - Popular templates ranking
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with NodeTemplate model"""
        super().__init__(NodeTemplate, session)

    async def find_by_type(
        self,
        node_type: NodeTypeCategory,
        skip: int = 0,
        limit: int = 100,
        enabled_only: bool = False
    ) -> List[NodeTemplate]:
        """
        Get node templates by type.

        Args:
            node_type: Node type category (INDICATOR, SIGNAL, etc.)
            skip: Number of records to skip
            limit: Maximum number of records to return
            enabled_only: Filter only enabled templates (future use)

        Returns:
            List of node templates of the specified type
        """
        stmt = select(NodeTemplate).where(
            NodeTemplate.node_type == node_type.value,
            NodeTemplate.is_deleted == False
        )

        # Order by usage count (most used first)
        stmt = stmt.order_by(NodeTemplate.usage_count.desc())
        stmt = stmt.offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        templates = list(result.scalars().all())

        logger.debug(f"Found {len(templates)} templates of type {node_type.value}")
        return templates

    async def find_by_user_and_type(
        self,
        user_id: str,
        node_type: NodeTypeCategory,
        skip: int = 0,
        limit: int = 100
    ) -> List[NodeTemplate]:
        """
        Get user's custom templates by type.

        Args:
            user_id: User ID
            node_type: Node type category
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of user's custom templates
        """
        stmt = select(NodeTemplate).where(
            NodeTemplate.user_id == user_id,
            NodeTemplate.node_type == node_type.value,
            NodeTemplate.is_deleted == False
        )

        stmt = stmt.order_by(NodeTemplate.created_at.desc())
        stmt = stmt.offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        templates = list(result.scalars().all())

        logger.debug(
            f"Found {len(templates)} templates for user {user_id} of type {node_type.value}"
        )
        return templates

    async def search(
        self,
        keyword: Optional[str] = None,
        node_type: Optional[NodeTypeCategory] = None,
        category: Optional[str] = None,
        is_system_template: Optional[bool] = None,
        user_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[NodeTemplate]:
        """
        Search node templates with multiple filters.

        Args:
            keyword: Search keyword (matches name or display_name)
            node_type: Filter by node type
            category: Filter by category
            is_system_template: Filter system vs custom templates
            user_id: Filter by user ID (for custom templates)
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of matching templates
        """
        stmt = select(NodeTemplate).where(
            NodeTemplate.is_deleted == False
        )

        # Apply keyword search
        if keyword:
            search_pattern = f"%{keyword}%"
            stmt = stmt.where(
                or_(
                    NodeTemplate.name.like(search_pattern),
                    NodeTemplate.display_name.like(search_pattern),
                    NodeTemplate.description.like(search_pattern)
                )
            )

        # Apply type filter
        if node_type:
            stmt = stmt.where(NodeTemplate.node_type == node_type.value)

        # Apply category filter
        if category:
            stmt = stmt.where(NodeTemplate.category == category)

        # Apply system/custom filter
        if is_system_template is not None:
            stmt = stmt.where(NodeTemplate.is_system_template == is_system_template)

        # Apply user filter
        if user_id:
            stmt = stmt.where(NodeTemplate.user_id == user_id)

        # Order by usage count, then by creation date
        stmt = stmt.order_by(
            NodeTemplate.usage_count.desc(),
            NodeTemplate.created_at.desc()
        )
        stmt = stmt.offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        templates = list(result.scalars().all())

        logger.debug(f"Search returned {len(templates)} templates")
        return templates

    async def increment_usage(
        self,
        template_id: str,
        commit: bool = True
    ) -> Optional[NodeTemplate]:
        """
        Atomically increment usage count for a template.

        Args:
            template_id: Template ID
            commit: Whether to commit the transaction

        Returns:
            Updated template or None if not found
        """
        # First check if template exists
        template = await self.get(template_id)
        if not template:
            logger.warning(f"Template not found: {template_id}")
            return None

        # Use atomic update to avoid race conditions
        stmt = (
            update(NodeTemplate)
            .where(NodeTemplate.id == template_id)
            .values(usage_count=NodeTemplate.usage_count + 1)
        )

        await self.session.execute(stmt)

        if commit:
            await self.session.commit()

        # Refresh to get updated value
        await self.session.refresh(template)

        logger.debug(
            f"Incremented usage count for template {template_id} to {template.usage_count}"
        )
        return template

    async def get_system_templates(
        self,
        node_type: Optional[NodeTypeCategory] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[NodeTemplate]:
        """
        Get system built-in templates.

        Args:
            node_type: Optional filter by node type
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of system templates
        """
        stmt = select(NodeTemplate).where(
            NodeTemplate.is_deleted == False,
            NodeTemplate.is_system_template == True
        )

        if node_type:
            stmt = stmt.where(NodeTemplate.node_type == node_type.value)

        stmt = stmt.order_by(NodeTemplate.usage_count.desc())
        stmt = stmt.offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        templates = list(result.scalars().all())

        logger.debug(f"Retrieved {len(templates)} system templates")
        return templates

    async def get_user_templates(
        self,
        user_id: str,
        node_type: Optional[NodeTypeCategory] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[NodeTemplate]:
        """
        Get user's custom templates.

        Args:
            user_id: User ID
            node_type: Optional filter by node type
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of user's custom templates
        """
        stmt = select(NodeTemplate).where(
            NodeTemplate.is_deleted == False,
            NodeTemplate.user_id == user_id
        )

        if node_type:
            stmt = stmt.where(NodeTemplate.node_type == node_type.value)

        stmt = stmt.order_by(NodeTemplate.created_at.desc())
        stmt = stmt.offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        templates = list(result.scalars().all())

        logger.debug(f"Retrieved {len(templates)} templates for user {user_id}")
        return templates
