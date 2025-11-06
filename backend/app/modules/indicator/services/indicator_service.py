"""
IndicatorService - Business logic for indicator operations

Provides high-level operations for managing technical indicators.
"""

from typing import Dict, Any, List, Optional
from loguru import logger

from app.database.repositories.indicator_repository import IndicatorRepository
from app.database.models.indicator import IndicatorCategory, IndicatorSource


class IndicatorService:
    """
    Service for indicator operations.

    Provides business logic for:
    - Indicator discovery and search
    - Category and source filtering
    - Usage tracking
    - Popular indicators
    """

    def __init__(self, indicator_repo: IndicatorRepository):
        """
        Initialize service with repository.

        Args:
            indicator_repo: IndicatorRepository instance
        """
        self.indicator_repo = indicator_repo

    async def get_indicators_by_category(
        self,
        category: str,
        skip: int = 0,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get indicators by category with pagination.

        Args:
            category: Indicator category
            skip: Skip records
            limit: Limit records

        Returns:
            Dict with indicators list and total count
        """
        try:
            indicators = await self.indicator_repo.get_by_category(
                category=IndicatorCategory(category),
                skip=skip,
                limit=limit
            )

            return {
                "indicators": [self._to_dict(ind) for ind in indicators],
                "total": len(indicators),
                "skip": skip,
                "limit": limit
            }
        except Exception as e:
            logger.error(f"Error getting indicators by category: {e}")
            raise

    async def search_indicators(
        self,
        keyword: str,
        skip: int = 0,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Search indicators by keyword.

        Args:
            keyword: Search keyword
            skip: Skip records
            limit: Limit records

        Returns:
            Dict with search results and total count
        """
        try:
            indicators = await self.indicator_repo.search_by_name(
                keyword=keyword,
                skip=skip,
                limit=limit
            )

            return {
                "indicators": [self._to_dict(ind) for ind in indicators],
                "total": len(indicators),
                "keyword": keyword,
                "skip": skip,
                "limit": limit
            }
        except Exception as e:
            logger.error(f"Error searching indicators: {e}")
            raise

    async def get_indicator_detail(self, indicator_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about an indicator.

        Args:
            indicator_id: Indicator ID

        Returns:
            Indicator details or None if not found
        """
        try:
            indicator = await self.indicator_repo.get(indicator_id)
            if not indicator:
                return None

            return self._to_dict(indicator)
        except Exception as e:
            logger.error(f"Error getting indicator detail: {e}")
            raise

    async def increment_usage(self, indicator_id: str) -> bool:
        """
        Increment indicator usage count.

        Args:
            indicator_id: Indicator ID

        Returns:
            Success status
        """
        try:
            result = await self.indicator_repo.increment_usage_count(indicator_id)
            return result is not None
        except Exception as e:
            logger.error(f"Error incrementing indicator usage: {e}")
            return False

    async def get_popular_indicators(
        self,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get popular indicators by usage count.

        Args:
            limit: Number of indicators to return

        Returns:
            Dict with popular indicators
        """
        try:
            indicators = await self.indicator_repo.get_popular_indicators(limit=limit)

            return {
                "indicators": [self._to_dict(ind) for ind in indicators],
                "total": len(indicators)
            }
        except Exception as e:
            logger.error(f"Error getting popular indicators: {e}")
            raise

    async def validate_indicator_exists(self, indicator_id: str) -> bool:
        """
        Validate that an indicator exists and is enabled.

        Args:
            indicator_id: Indicator ID

        Returns:
            True if indicator exists and is enabled
        """
        try:
            indicator = await self.indicator_repo.get(indicator_id)
            return indicator is not None and indicator.is_enabled
        except Exception as e:
            logger.error(f"Error validating indicator: {e}")
            return False

    async def get_indicator_categories(self) -> Dict[str, Any]:
        """
        Get all available indicator categories.

        Returns:
            Dict with category information
        """
        try:
            categories = [
                {
                    "value": category.value,
                    "label": category.name
                }
                for category in IndicatorCategory
            ]

            return {
                "categories": categories,
                "total": len(categories)
            }
        except Exception as e:
            logger.error(f"Error getting indicator categories: {e}")
            raise

    def _to_dict(self, indicator) -> Dict[str, Any]:
        """
        Convert indicator model to dictionary.

        Args:
            indicator: IndicatorComponent model instance

        Returns:
            Dictionary representation
        """
        return {
            "id": indicator.id,
            "code": indicator.code,
            "name_zh": indicator.name_zh,
            "name_en": indicator.name_en,
            "category": indicator.category,
            "source": indicator.source,
            "description_zh": indicator.description_zh,
            "description_en": indicator.description_en,
            "formula": indicator.formula,
            "parameters": indicator.parameters,
            "default_params": indicator.default_params,
            "usage_count": indicator.usage_count,
            "is_enabled": indicator.is_enabled,
            "created_at": indicator.created_at.isoformat() if indicator.created_at else None,
            "updated_at": indicator.updated_at.isoformat() if indicator.updated_at else None
        }
