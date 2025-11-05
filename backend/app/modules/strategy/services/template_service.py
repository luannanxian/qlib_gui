"""
TemplateService

Business logic for strategy template management:
- Get popular templates
- Add/update template ratings
- Calculate rating statistics
- Toggle favorites (future enhancement)
"""

from typing import List, Optional
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.strategy import StrategyTemplate, TemplateRating, StrategyCategory
from app.database.repositories.strategy_template import StrategyTemplateRepository
from app.database.repositories.template_rating import TemplateRatingRepository


class TemplateService:
    """Service for template management and rating operations"""

    def __init__(self, db: AsyncSession):
        """
        Initialize service with database session

        Args:
            db: AsyncSession for database operations
        """
        self.db = db
        self.template_repo = StrategyTemplateRepository(db)
        self.rating_repo = TemplateRatingRepository(db)

    async def get_popular_templates(
        self,
        limit: int = 5,
        category: Optional[StrategyCategory] = None
    ) -> List[StrategyTemplate]:
        """
        Get top N popular templates sorted by usage_count

        Args:
            limit: Maximum number of templates to return (default: 5)
            category: Optional category filter

        Returns:
            List of popular templates sorted by usage_count descending

        Example:
            >>> templates = await service.get_popular_templates(limit=10)
            >>> trend_templates = await service.get_popular_templates(
            ...     limit=5, category=StrategyCategory.TREND_FOLLOWING
            ... )
        """
        # Convert enum to string for repository
        category_str = category.value if category else None

        templates = await self.template_repo.get_popular(
            limit=limit,
            category=category_str
        )

        logger.debug(
            f"Retrieved {len(templates)} popular templates"
            f"{f' for category {category_str}' if category_str else ''}"
        )

        return templates

    async def add_rating(
        self,
        template_id: str,
        user_id: str,
        rating: int,
        comment: Optional[str] = None
    ) -> TemplateRating:
        """
        Add or update a rating for a template and recalculate statistics

        This method:
        1. Validates the rating value (1-5)
        2. Validates template exists
        3. Upserts the rating (create new or update existing)
        4. Recalculates template rating statistics
        5. Updates the template with new statistics

        Args:
            template_id: Template ID to rate
            user_id: User ID submitting the rating
            rating: Rating value (1-5)
            comment: Optional comment

        Returns:
            Created or updated TemplateRating

        Raises:
            ValueError: If rating is not between 1-5 or template not found

        Example:
            >>> rating = await service.add_rating(
            ...     template_id="template-123",
            ...     user_id="user-456",
            ...     rating=5,
            ...     comment="Excellent strategy!"
            ... )
        """
        # Validate rating
        if rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5")

        # Validate template exists
        template = await self.template_repo.get(template_id)
        if template is None:
            raise ValueError(f"Template not found: {template_id}")

        # Upsert rating
        rating_obj = await self.rating_repo.upsert_rating(
            template_id=template_id,
            user_id=user_id,
            rating=rating,
            comment=comment
        )

        logger.info(
            f"Rating {'updated' if rating_obj.updated_at else 'created'} "
            f"for template {template_id} by user {user_id}: {rating}/5"
        )

        # Recalculate template statistics
        await self._recalculate_template_rating(template_id)

        return rating_obj

    async def _recalculate_template_rating(self, template_id: str) -> None:
        """
        Recalculate and update template rating statistics

        Queries all ratings for the template and calculates:
        - rating_average: Average of all ratings
        - rating_count: Total number of ratings

        Args:
            template_id: Template ID to recalculate

        Note:
            This is an internal method called after rating changes
        """
        # Get all ratings for this template
        ratings = await self.rating_repo.get_by_template(template_id, limit=1000)

        if not ratings:
            # No ratings, set to defaults
            rating_average = 0.0
            rating_count = 0
        else:
            # Calculate average
            total_rating = sum(r.rating for r in ratings)
            rating_count = len(ratings)
            rating_average = total_rating / rating_count

        # Update template statistics
        await self.template_repo.update_rating_stats(
            id=template_id,
            rating_average=rating_average,
            rating_count=rating_count
        )

        logger.debug(
            f"Updated template {template_id} rating stats: "
            f"avg={rating_average:.2f}, count={rating_count}"
        )

    async def toggle_favorite(
        self,
        template_id: str,
        user_id: str
    ) -> bool:
        """
        Toggle favorite status for a template

        NOTE: This is a placeholder for future implementation.
        Requires adding UserFavorite model or user preferences table.

        Args:
            template_id: Template ID
            user_id: User ID

        Returns:
            True if now favorited, False if unfavorited

        Raises:
            NotImplementedError: This feature is not yet implemented
        """
        raise NotImplementedError(
            "Favorite functionality requires UserFavorite model implementation"
        )
