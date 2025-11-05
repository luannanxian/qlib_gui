"""
User Factor Library Repository

Repository for managing users' personal factor libraries with favorites
and usage tracking.
"""

from typing import List, Optional
from datetime import datetime, timezone

from loguru import logger
from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.indicator import UserFactorLibrary, LibraryItemStatus
from app.database.repositories.base import BaseRepository


class UserFactorLibraryRepository(BaseRepository[UserFactorLibrary]):
    """
    Repository for UserFactorLibrary operations.

    Provides specialized methods for:
    - User library management
    - Favorites tracking
    - Usage statistics
    - Library item organization
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with UserFactorLibrary model"""
        super().__init__(UserFactorLibrary, session)

    async def get_user_library(
        self,
        user_id: str,
        item_type: Optional[str] = None,  # "factor" or "indicator"
        status: Optional[str] = None,
        is_favorite: Optional[bool] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[UserFactorLibrary]:
        """Get user's library items with filters"""
        from sqlalchemy import desc

        conditions = [
            self.model.user_id == user_id,
            self.model.is_deleted == False
        ]

        if item_type == "factor":
            conditions.append(self.model.factor_id.isnot(None))
        elif item_type == "indicator":
            conditions.append(self.model.component_id.isnot(None))

        if status:
            conditions.append(self.model.status == status)

        if is_favorite is not None:
            conditions.append(self.model.is_favorite == is_favorite)

        stmt = select(self.model).where(and_(*conditions)).order_by(
            desc(self.model.updated_at)
        ).offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_favorites(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 20
    ) -> List[UserFactorLibrary]:
        """Get user's favorite items"""
        return await self.get_user_library(
            user_id=user_id,
            is_favorite=True,
            skip=skip,
            limit=limit
        )

    async def add_to_library(
        self,
        user_id: str,
        factor_id: Optional[str] = None,
        component_id: Optional[str] = None,
        is_favorite: bool = False
    ) -> Optional[UserFactorLibrary]:
        """Add item to user's library"""
        if not (factor_id or component_id) or (factor_id and component_id):
            return None

        existing = await self.find_library_item(
            user_id=user_id,
            factor_id=factor_id,
            component_id=component_id
        )

        if existing:
            existing.is_favorite = is_favorite
            existing.status = LibraryItemStatus.ACTIVE.value
            await self.session.commit()
            await self.session.refresh(existing)
            return existing

        library_data = {
            "user_id": user_id,
            "factor_id": factor_id,
            "component_id": component_id,
            "is_favorite": is_favorite,
            "status": LibraryItemStatus.ACTIVE.value
        }

        return await self.create(library_data, commit=True)

    async def toggle_favorite(
        self,
        library_item_id: str
    ) -> Optional[UserFactorLibrary]:
        """Toggle favorite status"""
        item = await self.get(library_item_id)
        if not item:
            return None

        item.is_favorite = not item.is_favorite
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def increment_usage_count(
        self,
        library_item_id: str
    ) -> bool:
        """Increment usage count"""
        item = await self.get(library_item_id)
        if not item:
            return False

        item.usage_count += 1
        item.last_used_at = datetime.now(timezone.utc)
        await self.session.commit()
        return True

    async def find_library_item(
        self,
        user_id: str,
        factor_id: Optional[str] = None,
        component_id: Optional[str] = None
    ) -> Optional[UserFactorLibrary]:
        """Find library item by user and factor/component"""
        conditions = [
            self.model.user_id == user_id,
            self.model.is_deleted == False
        ]

        if factor_id:
            conditions.append(self.model.factor_id == factor_id)
        if component_id:
            conditions.append(self.model.component_id == component_id)

        stmt = select(self.model).where(and_(*conditions)).limit(1)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def remove_from_library(
        self,
        library_item_id: str,
        soft: bool = True
    ) -> bool:
        """Remove item from library"""
        return await self.delete(library_item_id, soft=soft)

    async def get_most_used(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[UserFactorLibrary]:
        """Get user's most used library items"""
        from sqlalchemy import desc

        stmt = select(self.model).where(
            and_(
                self.model.user_id == user_id,
                self.model.is_deleted == False,
                self.model.usage_count > 0
            )
        ).order_by(
            desc(self.model.usage_count)
        ).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())
