"""
TemplateRating Repository

Handles database operations for template ratings including:
- CRUD operations
- Get ratings by template
- Get user-specific rating
- Upsert (insert or update) rating
"""

from typing import List, Optional
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.strategy import TemplateRating
from app.database.repositories.base import BaseRepository


class TemplateRatingRepository(BaseRepository[TemplateRating]):
    """Repository for TemplateRating model operations"""

    def __init__(self, db: AsyncSession):
        super().__init__(TemplateRating, db)

    async def get_by_template(
        self,
        template_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[TemplateRating]:
        """
        Get all ratings for a template

        Args:
            template_id: Template ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of ratings sorted by creation date descending
        """
        query = (
            select(TemplateRating)
            .where(
                and_(
                    TemplateRating.template_id == template_id,
                    TemplateRating.is_deleted == False
                )
            )
            .order_by(desc(TemplateRating.created_at))
            .offset(skip)
            .limit(limit)
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_user_rating(
        self,
        template_id: str,
        user_id: str
    ) -> Optional[TemplateRating]:
        """
        Get a specific user's rating for a template

        Args:
            template_id: Template ID
            user_id: User ID

        Returns:
            User's rating or None if not found
        """
        query = (
            select(TemplateRating)
            .where(
                and_(
                    TemplateRating.template_id == template_id,
                    TemplateRating.user_id == user_id,
                    TemplateRating.is_deleted == False
                )
            )
        )

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def upsert_rating(
        self,
        template_id: str,
        user_id: str,
        rating: int,
        comment: Optional[str] = None
    ) -> TemplateRating:
        """
        Insert or update a user's rating for a template

        If the user has already rated the template, update the existing rating.
        Otherwise, create a new rating.

        Args:
            template_id: Template ID
            user_id: User ID
            rating: Rating value (1-5)
            comment: Optional comment

        Returns:
            The created or updated rating
        """
        # Check if rating already exists
        existing = await self.get_user_rating(template_id, user_id)

        if existing:
            # Update existing rating
            update_data = {"rating": rating}
            if comment is not None:
                update_data["comment"] = comment

            updated = await self.update(existing.id, update_data, user_id=user_id)
            return updated
        else:
            # Create new rating
            rating_data = {
                "template_id": template_id,
                "user_id": user_id,
                "rating": rating
            }
            if comment is not None:
                rating_data["comment"] = comment

            created = await self.create(rating_data, user_id=user_id)
            return created
