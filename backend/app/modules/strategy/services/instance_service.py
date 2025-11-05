"""
InstanceService

Business logic for strategy instance management:
- Create strategies from templates
- Create custom strategies
- Duplicate strategies
- Version management (snapshots and restore)
- Strategy lifecycle operations
"""

from typing import List, Optional, Dict, Any
from copy import deepcopy
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.strategy import StrategyInstance, StrategyStatus
from app.database.repositories.strategy_instance import StrategyInstanceRepository
from app.database.repositories.strategy_template import StrategyTemplateRepository


class InstanceService:
    """Service for strategy instance management and version control"""

    MAX_VERSIONS = 5  # Maximum number of version snapshots to retain

    def __init__(self, db: AsyncSession):
        """
        Initialize service with database session

        Args:
            db: AsyncSession for database operations
        """
        self.db = db
        self.instance_repo = StrategyInstanceRepository(db)
        self.template_repo = StrategyTemplateRepository(db)

    async def create_from_template(
        self,
        template_id: str,
        user_id: str,
        name: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> StrategyInstance:
        """
        Create a strategy instance from a template

        This method:
        1. Retrieves the template
        2. Clones the template's logic_flow (deep copy)
        3. Merges default parameters with user-provided parameters
        4. Creates a new strategy instance with version=1
        5. Increments the template's usage_count

        Args:
            template_id: Template ID to clone from
            user_id: User ID creating the strategy
            name: Name for the new strategy instance
            parameters: Optional parameter overrides

        Returns:
            Created strategy instance

        Raises:
            ValueError: If template not found

        Example:
            >>> instance = await service.create_from_template(
            ...     template_id="template-123",
            ...     user_id="user-456",
            ...     name="My MA Strategy",
            ...     parameters={"ma_short_period": 10}
            ... )
        """
        # Get template
        template = await self.template_repo.get(template_id)
        if template is None:
            raise ValueError(f"Template not found: {template_id}")

        # Clone logic_flow (deep copy to avoid mutation)
        logic_flow = deepcopy(template.logic_flow)

        # Merge parameters: template defaults + user overrides
        instance_parameters = {}

        # Extract default values from template parameter definitions
        for param_name, param_def in template.parameters.items():
            instance_parameters[param_name] = param_def.get("default")

        # Override with user-provided parameters
        if parameters:
            instance_parameters.update(parameters)

        # Create strategy instance
        instance_data = {
            "name": name,
            "user_id": user_id,
            "template_id": template_id,
            "logic_flow": logic_flow,
            "parameters": instance_parameters,
            "status": StrategyStatus.DRAFT,
            "version": 1,
            "parent_version_id": None
        }

        instance = await self.instance_repo.create(instance_data, user_id=user_id)

        # Increment template usage count
        await self.template_repo.increment_usage_count(template_id)

        logger.info(
            f"Created strategy instance '{name}' from template {template_id} "
            f"for user {user_id}"
        )

        return instance

    async def create_custom(
        self,
        user_id: str,
        name: str,
        logic_flow: Dict,
        parameters: Dict[str, Any]
    ) -> StrategyInstance:
        """
        Create a custom strategy without using a template

        Args:
            user_id: User ID creating the strategy
            name: Strategy name
            logic_flow: Custom logic flow structure
            parameters: Custom parameters

        Returns:
            Created strategy instance

        Example:
            >>> instance = await service.create_custom(
            ...     user_id="user-123",
            ...     name="Custom RSI Strategy",
            ...     logic_flow={"nodes": [...], "edges": [...]},
            ...     parameters={"rsi_period": 14}
            ... )
        """
        instance_data = {
            "name": name,
            "user_id": user_id,
            "template_id": None,  # Custom strategy has no template
            "logic_flow": logic_flow,
            "parameters": parameters,
            "status": StrategyStatus.DRAFT,
            "version": 1,
            "parent_version_id": None
        }

        instance = await self.instance_repo.create(instance_data, user_id=user_id)

        logger.info(f"Created custom strategy '{name}' for user {user_id}")

        return instance

    async def duplicate_strategy(
        self,
        strategy_id: str,
        user_id: str,
        new_name: str
    ) -> StrategyInstance:
        """
        Duplicate an existing strategy as a new instance

        Creates a copy of the strategy with a new name. The duplicate
        is a completely independent instance with version=1.

        Args:
            strategy_id: ID of strategy to duplicate
            user_id: User ID performing duplication
            new_name: Name for the duplicated strategy

        Returns:
            New strategy instance (copy)

        Raises:
            ValueError: If strategy not found or user doesn't have access

        Example:
            >>> duplicate = await service.duplicate_strategy(
            ...     strategy_id="strategy-123",
            ...     user_id="user-456",
            ...     new_name="Copy of My Strategy"
            ... )
        """
        # Get original strategy
        original = await self.instance_repo.get(strategy_id)

        if original is None:
            raise ValueError(f"Strategy not found: {strategy_id}")

        # Verify ownership
        if original.user_id != user_id:
            raise ValueError(
                f"Strategy not found or access denied: {strategy_id}"
            )

        # Create duplicate with deep copy of logic_flow and parameters
        duplicate_data = {
            "name": new_name,
            "user_id": user_id,
            "template_id": original.template_id,
            "logic_flow": deepcopy(original.logic_flow),
            "parameters": deepcopy(original.parameters),
            "status": StrategyStatus.DRAFT,
            "version": 1,
            "parent_version_id": None
        }

        duplicate = await self.instance_repo.create(duplicate_data, user_id=user_id)

        logger.info(
            f"Duplicated strategy {strategy_id} as '{new_name}' "
            f"for user {user_id}"
        )

        return duplicate

    async def save_snapshot(
        self,
        strategy_id: str,
        user_id: str
    ) -> StrategyInstance:
        """
        Save a version snapshot of the strategy

        Creates a snapshot with:
        - parent_version_id = strategy_id
        - version = current_max_version + 1
        - Same logic_flow and parameters as parent

        Maintains a maximum of 5 snapshots. If limit exceeded,
        deletes the oldest snapshot.

        Args:
            strategy_id: Strategy ID to snapshot
            user_id: User ID performing the snapshot

        Returns:
            Created snapshot instance

        Raises:
            ValueError: If strategy not found or access denied

        Example:
            >>> snapshot = await service.save_snapshot(
            ...     strategy_id="strategy-123",
            ...     user_id="user-456"
            ... )
        """
        # Get current strategy
        strategy = await self.instance_repo.get(strategy_id)

        if strategy is None:
            raise ValueError(f"Strategy not found: {strategy_id}")

        # Verify ownership
        if strategy.user_id != user_id:
            raise ValueError(
                f"Strategy not found or access denied: {strategy_id}"
            )

        # Get existing versions for this strategy
        existing_versions = await self.instance_repo.get_versions(strategy_id)

        # Check if we need to delete oldest version (keep max 5)
        if len(existing_versions) >= self.MAX_VERSIONS:
            # Sort by version number to find oldest (lowest version number)
            oldest = min(existing_versions, key=lambda v: v.version)
            await self.instance_repo.delete(oldest.id, user_id=user_id)

            # Flush to ensure delete is processed
            await self.db.flush()

            # Refetch versions after deletion
            existing_versions = await self.instance_repo.get_versions(strategy_id)

            logger.debug(
                f"Deleted oldest snapshot {oldest.id} to maintain max "
                f"{self.MAX_VERSIONS} versions"
            )

        # Calculate next version number
        if existing_versions:
            max_version = max(v.version for v in existing_versions)
            next_version = max_version + 1
        else:
            next_version = strategy.version + 1

        # Create snapshot
        snapshot_data = {
            "name": strategy.name,
            "user_id": user_id,
            "template_id": strategy.template_id,
            "logic_flow": deepcopy(strategy.logic_flow),
            "parameters": deepcopy(strategy.parameters),
            "status": strategy.status,
            "version": next_version,
            "parent_version_id": strategy_id
        }

        snapshot = await self.instance_repo.create(snapshot_data, user_id=user_id)

        logger.info(
            f"Saved snapshot version {next_version} for strategy {strategy_id}"
        )

        return snapshot

    async def restore_snapshot(
        self,
        strategy_id: str,
        version_id: str,
        user_id: str
    ) -> StrategyInstance:
        """
        Restore strategy to a previous snapshot version

        Updates the current strategy's logic_flow and parameters
        from the specified snapshot version.

        Args:
            strategy_id: Current strategy ID
            version_id: Snapshot version ID to restore from
            user_id: User ID performing the restore

        Returns:
            Updated strategy instance

        Raises:
            ValueError: If strategy/snapshot not found or access denied

        Example:
            >>> restored = await service.restore_snapshot(
            ...     strategy_id="strategy-123",
            ...     version_id="version-456",
            ...     user_id="user-789"
            ... )
        """
        # Get current strategy
        strategy = await self.instance_repo.get(strategy_id)
        if strategy is None or strategy.user_id != user_id:
            raise ValueError(
                f"Strategy not found or access denied: {strategy_id}"
            )

        # Get snapshot version
        snapshot = await self.instance_repo.get(version_id)
        if snapshot is None:
            raise ValueError(f"Snapshot not found: {version_id}")

        # Verify snapshot belongs to this strategy
        if snapshot.parent_version_id != strategy_id:
            raise ValueError(
                f"Snapshot {version_id} does not belong to strategy {strategy_id}"
            )

        # Verify ownership
        if snapshot.user_id != user_id:
            raise ValueError(f"Snapshot access denied: {version_id}")

        # Update strategy with snapshot data
        update_data = {
            "logic_flow": deepcopy(snapshot.logic_flow),
            "parameters": deepcopy(snapshot.parameters)
        }

        updated = await self.instance_repo.update(
            strategy_id,
            update_data,
            user_id=user_id
        )

        logger.info(
            f"Restored strategy {strategy_id} from snapshot {version_id} "
            f"(version {snapshot.version})"
        )

        return updated

    async def get_versions(
        self,
        strategy_id: str,
        user_id: str
    ) -> List[StrategyInstance]:
        """
        Get version history for a strategy

        Returns all snapshot versions sorted by creation time (newest first).

        Args:
            strategy_id: Strategy ID
            user_id: User ID (for authorization)

        Returns:
            List of version snapshots

        Raises:
            ValueError: If strategy not found or access denied

        Example:
            >>> versions = await service.get_versions(
            ...     strategy_id="strategy-123",
            ...     user_id="user-456"
            ... )
        """
        # Verify strategy exists and user has access
        strategy = await self.instance_repo.get(strategy_id)
        if strategy is None or strategy.user_id != user_id:
            raise ValueError(
                f"Strategy not found or access denied: {strategy_id}"
            )

        # Get all versions for this strategy
        versions = await self.instance_repo.get_versions(strategy_id)

        # Sort by created_at descending (newest first)
        versions.sort(key=lambda v: v.created_at, reverse=True)

        return versions
