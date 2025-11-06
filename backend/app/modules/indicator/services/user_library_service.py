"""
UserLibraryService - Business logic for user factor library operations

Provides high-level operations for managing user's personal factor library.
"""

from typing import Dict, Any, List, Optional
from loguru import logger

from app.database.repositories.user_factor_library_repository import UserFactorLibraryRepository


class UserLibraryService:
    """
    Service for user factor library operations.

    Provides business logic for:
    - Library item management (add, remove)
    - Favorite management
    - Usage tracking
    - Most used items discovery
    - Library statistics
    """

    def __init__(self, user_library_repo: UserFactorLibraryRepository):
        """
        Initialize service with repository.

        Args:
            user_library_repo: UserFactorLibraryRepository instance
        """
        self.user_library_repo = user_library_repo

    async def get_user_library(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get user's library items with pagination.

        Args:
            user_id: User ID
            skip: Skip records
            limit: Limit records

        Returns:
            Dict with library items and total count
        """
        try:
            items = await self.user_library_repo.get_user_library(
                user_id=user_id,
                skip=skip,
                limit=limit
            )

            return {
                "items": [self._to_dict(item) for item in items],
                "total": len(items),
                "skip": skip,
                "limit": limit
            }
        except Exception as e:
            logger.error(f"Error getting user library: {e}")
            raise

    async def add_to_library(
        self,
        user_id: str,
        factor_id: str
    ) -> Dict[str, Any]:
        """
        Add a factor to user's library.

        Args:
            user_id: User ID
            factor_id: Factor ID to add

        Returns:
            Dict with added library item
        """
        try:
            # Use repository's add_to_library method which handles duplicates
            item = await self.user_library_repo.add_to_library(
                user_id=user_id,
                factor_id=factor_id,
                is_favorite=False
            )

            if not item:
                logger.error(f"Failed to add factor {factor_id} to library for user {user_id}")
                raise ValueError("Failed to add item to library")

            return {
                "item": self._to_dict(item),
                "message": "Factor added to library"
            }
        except Exception as e:
            logger.error(f"Error adding to library: {e}")
            raise

    async def toggle_favorite(
        self,
        user_id: str,
        factor_id: str,
        is_favorite: bool
    ) -> Optional[Dict[str, Any]]:
        """
        Toggle favorite status of a library item.

        Args:
            user_id: User ID
            factor_id: Factor ID
            is_favorite: New favorite status

        Returns:
            Updated library item or None if not found/unauthorized
        """
        try:
            # Find the library item
            item = await self.user_library_repo.find_library_item(
                user_id=user_id,
                factor_id=factor_id
            )

            if not item:
                logger.warning(f"Library item not found for user {user_id}, factor {factor_id}")
                return None

            # Update favorite status directly
            item.is_favorite = is_favorite
            await self.user_library_repo.session.commit()
            await self.user_library_repo.session.refresh(item)

            return {
                "item": self._to_dict(item),
                "message": f"Favorite status updated to {is_favorite}"
            }
        except Exception as e:
            logger.error(f"Error toggling favorite: {e}")
            raise

    async def increment_usage(
        self,
        user_id: str,
        factor_id: str
    ) -> bool:
        """
        Increment usage count for a library item.

        Args:
            user_id: User ID
            factor_id: Factor ID

        Returns:
            Success status
        """
        try:
            # Find the library item
            item = await self.user_library_repo.find_library_item(
                user_id=user_id,
                factor_id=factor_id
            )

            if not item:
                logger.warning(f"Library item not found for user {user_id}, factor {factor_id}")
                return False

            result = await self.user_library_repo.increment_usage_count(item.id)
            return result
        except Exception as e:
            logger.error(f"Error incrementing library usage: {e}")
            return False

    async def get_favorites(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get user's favorite library items.

        Args:
            user_id: User ID
            skip: Skip records
            limit: Limit records

        Returns:
            Dict with favorite items
        """
        try:
            favorites = await self.user_library_repo.get_favorites(
                user_id=user_id,
                skip=skip,
                limit=limit
            )

            return {
                "items": [self._to_dict(item) for item in favorites],
                "total": len(favorites)
            }
        except Exception as e:
            logger.error(f"Error getting favorites: {e}")
            raise

    async def get_most_used(
        self,
        user_id: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get user's most used library items.

        Args:
            user_id: User ID
            limit: Number of items to return

        Returns:
            Dict with most used items
        """
        try:
            items = await self.user_library_repo.get_most_used(
                user_id=user_id,
                limit=limit
            )

            return {
                "items": [self._to_dict(item) for item in items],
                "total": len(items)
            }
        except Exception as e:
            logger.error(f"Error getting most used items: {e}")
            raise

    async def remove_from_library(
        self,
        user_id: str,
        factor_id: str
    ) -> bool:
        """
        Remove a factor from user's library.

        Args:
            user_id: User ID
            factor_id: Factor ID to remove

        Returns:
            Success status
        """
        try:
            # Find the library item
            item = await self.user_library_repo.find_library_item(
                user_id=user_id,
                factor_id=factor_id
            )

            if not item:
                logger.warning(f"Unauthorized removal attempt for user {user_id}, factor {factor_id}")
                return False

            # Remove from library
            return await self.user_library_repo.delete(item.id, soft=True)
        except Exception as e:
            logger.error(f"Error removing from library: {e}")
            return False

    async def get_library_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get statistics about user's library.

        Args:
            user_id: User ID

        Returns:
            Dict with library statistics
        """
        try:
            # Get all library items
            all_items = await self.user_library_repo.get_user_library(
                user_id=user_id,
                skip=0,
                limit=10000  # Get all items for stats
            )

            # Calculate statistics
            total_items = len(all_items)
            favorite_count = sum(1 for item in all_items if item.is_favorite)
            total_usage = sum(item.usage_count for item in all_items)

            return {
                "user_id": user_id,
                "total_items": total_items,
                "favorite_count": favorite_count,
                "total_usage": total_usage
            }
        except Exception as e:
            logger.error(f"Error getting library stats: {e}")
            raise

    def _to_dict(self, library_item) -> Dict[str, Any]:
        """
        Convert library item model to dictionary.

        Args:
            library_item: UserFactorLibrary model instance

        Returns:
            Dictionary representation
        """
        return {
            "id": library_item.id,
            "user_id": library_item.user_id,
            "factor_id": library_item.factor_id,
            "is_favorite": library_item.is_favorite,
            "usage_count": library_item.usage_count,
            "last_used_at": library_item.last_used_at.isoformat() if library_item.last_used_at else None,
            "created_at": library_item.created_at.isoformat() if library_item.created_at else None,
            "updated_at": library_item.updated_at.isoformat() if library_item.updated_at else None
        }
