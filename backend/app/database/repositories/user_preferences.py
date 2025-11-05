"""
User Preferences Repository

This module provides repository pattern implementation for UserPreferences model
with custom methods for user-specific settings management.
"""

from typing import Optional, List, Dict, Any

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user_preferences import UserPreferences, UserMode
from app.database.repositories.base import BaseRepository


class UserPreferencesRepository(BaseRepository[UserPreferences]):
    """
    Repository for UserPreferences model with specialized query methods.

    Extends BaseRepository with user preferences-specific operations such as:
    - Get or create preferences for a user
    - Update user mode
    - Manage completed guides
    - Update custom settings
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize user preferences repository.

        Args:
            session: Async database session
        """
        super().__init__(UserPreferences, session)

    async def get_by_user_id(
        self,
        user_id: str,
        include_deleted: bool = False
    ) -> Optional[UserPreferences]:
        """
        Get preferences by user ID.

        Args:
            user_id: User identifier
            include_deleted: Whether to include soft-deleted records

        Returns:
            UserPreferences instance or None if not found

        Example:
            prefs = await repo.get_by_user_id("user-123")
        """
        stmt = select(UserPreferences).where(UserPreferences.user_id == user_id)

        if not include_deleted:
            stmt = stmt.where(UserPreferences.is_deleted == False)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        user_id: str,
        defaults: Optional[Dict[str, Any]] = None
    ) -> tuple[UserPreferences, bool]:
        """
        Get existing preferences or create new ones with defaults.

        Args:
            user_id: User identifier
            defaults: Optional default values for new preferences

        Returns:
            Tuple of (UserPreferences instance, created boolean)
            - created is True if new preferences were created
            - created is False if existing preferences were found

        Example:
            prefs, created = await repo.get_or_create(
                "user-123",
                {"mode": "expert", "language": "zh"}
            )
        """
        # Try to get existing preferences
        existing = await self.get_by_user_id(user_id)
        if existing:
            return existing, False

        # Create new preferences
        prefs_data = {"user_id": user_id}
        if defaults:
            prefs_data.update(defaults)

        new_prefs = await self.create(prefs_data)
        logger.info(f"Created new preferences for user: {user_id}")
        return new_prefs, True

    async def update_mode(
        self,
        user_id: str,
        mode: UserMode | str,
        commit: bool = True
    ) -> Optional[UserPreferences]:
        """
        Update user mode (beginner/expert).

        Args:
            user_id: User identifier
            mode: New user mode
            commit: Whether to commit the transaction

        Returns:
            Updated UserPreferences instance or None if not found

        Example:
            prefs = await repo.update_mode("user-123", "expert")
        """
        prefs = await self.get_by_user_id(user_id)
        if prefs is None:
            logger.warning(f"User preferences not found: user_id={user_id}")
            return None

        # Convert enum to string if needed
        mode_str = mode.value if isinstance(mode, UserMode) else mode

        prefs.mode = mode_str

        if commit:
            await self.session.commit()
            await self.session.refresh(prefs)

        logger.debug(f"Updated mode for user {user_id} to {mode_str}")
        return prefs

    async def update_language(
        self,
        user_id: str,
        language: str,
        commit: bool = True
    ) -> Optional[UserPreferences]:
        """
        Update user language preference.

        Args:
            user_id: User identifier
            language: Language code (e.g., "en", "zh")
            commit: Whether to commit the transaction

        Returns:
            Updated UserPreferences instance or None if not found

        Example:
            prefs = await repo.update_language("user-123", "zh")
        """
        prefs = await self.get_by_user_id(user_id)
        if prefs is None:
            logger.warning(f"User preferences not found: user_id={user_id}")
            return None

        prefs.language = language

        if commit:
            await self.session.commit()
            await self.session.refresh(prefs)

        logger.debug(f"Updated language for user {user_id} to {language}")
        return prefs

    async def update_theme(
        self,
        user_id: str,
        theme: str,
        commit: bool = True
    ) -> Optional[UserPreferences]:
        """
        Update user theme preference.

        Args:
            user_id: User identifier
            theme: Theme name (e.g., "light", "dark")
            commit: Whether to commit the transaction

        Returns:
            Updated UserPreferences instance or None if not found

        Example:
            prefs = await repo.update_theme("user-123", "dark")
        """
        prefs = await self.get_by_user_id(user_id)
        if prefs is None:
            logger.warning(f"User preferences not found: user_id={user_id}")
            return None

        prefs.theme = theme

        if commit:
            await self.session.commit()
            await self.session.refresh(prefs)

        logger.debug(f"Updated theme for user {user_id} to {theme}")
        return prefs

    async def toggle_tooltips(
        self,
        user_id: str,
        commit: bool = True
    ) -> Optional[UserPreferences]:
        """
        Toggle tooltip display preference.

        Args:
            user_id: User identifier
            commit: Whether to commit the transaction

        Returns:
            Updated UserPreferences instance or None if not found

        Example:
            prefs = await repo.toggle_tooltips("user-123")
        """
        prefs = await self.get_by_user_id(user_id)
        if prefs is None:
            logger.warning(f"User preferences not found: user_id={user_id}")
            return None

        prefs.show_tooltips = not prefs.show_tooltips

        if commit:
            await self.session.commit()
            await self.session.refresh(prefs)

        logger.debug(f"Toggled tooltips for user {user_id} to {prefs.show_tooltips}")
        return prefs

    async def add_completed_guide(
        self,
        user_id: str,
        guide_id: str,
        commit: bool = True
    ) -> Optional[UserPreferences]:
        """
        Add a guide ID to the list of completed guides.

        Args:
            user_id: User identifier
            guide_id: Guide identifier to mark as completed
            commit: Whether to commit the transaction

        Returns:
            Updated UserPreferences instance or None if not found

        Example:
            prefs = await repo.add_completed_guide("user-123", "intro-tour")
        """
        prefs = await self.get_by_user_id(user_id)
        if prefs is None:
            logger.warning(f"User preferences not found: user_id={user_id}")
            return None

        # Get current completed guides
        completed_guides = prefs.completed_guides or []

        # Add guide if not already present
        if guide_id not in completed_guides:
            completed_guides.append(guide_id)
            prefs.completed_guides = completed_guides

            if commit:
                await self.session.commit()
                await self.session.refresh(prefs)

            logger.debug(f"Added completed guide {guide_id} for user {user_id}")

        return prefs

    async def remove_completed_guide(
        self,
        user_id: str,
        guide_id: str,
        commit: bool = True
    ) -> Optional[UserPreferences]:
        """
        Remove a guide ID from the list of completed guides.

        Args:
            user_id: User identifier
            guide_id: Guide identifier to remove
            commit: Whether to commit the transaction

        Returns:
            Updated UserPreferences instance or None if not found

        Example:
            prefs = await repo.remove_completed_guide("user-123", "intro-tour")
        """
        prefs = await self.get_by_user_id(user_id)
        if prefs is None:
            logger.warning(f"User preferences not found: user_id={user_id}")
            return None

        # Get current completed guides
        completed_guides = prefs.completed_guides or []

        # Remove guide if present
        if guide_id in completed_guides:
            completed_guides.remove(guide_id)
            prefs.completed_guides = completed_guides

            if commit:
                await self.session.commit()
                await self.session.refresh(prefs)

            logger.debug(f"Removed completed guide {guide_id} for user {user_id}")

        return prefs

    async def has_completed_guide(
        self,
        user_id: str,
        guide_id: str
    ) -> bool:
        """
        Check if a user has completed a specific guide.

        Args:
            user_id: User identifier
            guide_id: Guide identifier to check

        Returns:
            True if guide is completed, False otherwise

        Example:
            completed = await repo.has_completed_guide("user-123", "intro-tour")
        """
        prefs = await self.get_by_user_id(user_id)
        if prefs is None:
            return False

        completed_guides = prefs.completed_guides or []
        return guide_id in completed_guides

    async def update_settings(
        self,
        user_id: str,
        settings_update: Dict[str, Any],
        merge: bool = True,
        commit: bool = True
    ) -> Optional[UserPreferences]:
        """
        Update custom settings for a user.

        Args:
            user_id: User identifier
            settings_update: Dictionary with settings to update
            merge: If True, merge with existing settings; if False, replace entirely
            commit: Whether to commit the transaction

        Returns:
            Updated UserPreferences instance or None if not found

        Example:
            prefs = await repo.update_settings(
                "user-123",
                {"chart_default_type": "kline", "auto_refresh": True}
            )
        """
        prefs = await self.get_by_user_id(user_id)
        if prefs is None:
            logger.warning(f"User preferences not found: user_id={user_id}")
            return None

        if merge:
            # Merge with existing settings
            current_settings = prefs.settings or {}
            current_settings.update(settings_update)
            prefs.settings = current_settings
        else:
            # Replace settings entirely
            prefs.settings = settings_update

        if commit:
            await self.session.commit()
            await self.session.refresh(prefs)

        logger.debug(f"Updated settings for user {user_id}")
        return prefs

    async def get_setting(
        self,
        user_id: str,
        setting_key: str,
        default: Any = None
    ) -> Any:
        """
        Get a specific setting value for a user.

        Args:
            user_id: User identifier
            setting_key: Setting key to retrieve
            default: Default value if setting not found

        Returns:
            Setting value or default

        Example:
            chart_type = await repo.get_setting(
                "user-123",
                "chart_default_type",
                default="line"
            )
        """
        prefs = await self.get_by_user_id(user_id)
        if prefs is None:
            return default

        settings = prefs.settings or {}
        return settings.get(setting_key, default)

    async def get_all_by_mode(
        self,
        mode: UserMode | str,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False
    ) -> List[UserPreferences]:
        """
        Get all users with a specific mode.

        Args:
            mode: User mode (beginner/expert)
            skip: Number of records to skip
            limit: Maximum number of records to return
            include_deleted: Whether to include soft-deleted records

        Returns:
            List of UserPreferences instances

        Example:
            expert_users = await repo.get_all_by_mode("expert")
        """
        mode_str = mode.value if isinstance(mode, UserMode) else mode

        stmt = select(UserPreferences).where(UserPreferences.mode == mode_str)

        if not include_deleted:
            stmt = stmt.where(UserPreferences.is_deleted == False)

        stmt = stmt.order_by(UserPreferences.created_at.desc()).offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())
