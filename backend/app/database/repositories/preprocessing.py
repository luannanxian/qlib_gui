"""
Data Preprocessing Repositories

Data access layer for DataPreprocessingRule and DataPreprocessingTask models
with async SQLAlchemy operations.
"""

from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.base import BaseRepository
from app.database.models.preprocessing import (
    DataPreprocessingRule,
    DataPreprocessingTask,
    PreprocessingRuleType,
    PreprocessingTaskStatus,
)


class PreprocessingRuleRepository(BaseRepository[DataPreprocessingRule]):
    """
    Repository for DataPreprocessingRule model with specialized query methods

    Handles:
    - Template management (max 20 templates per user)
    - Rule creation and retrieval
    - Template usage tracking
    """

    def __init__(self, session: AsyncSession):
        super().__init__(DataPreprocessingRule, session)

    async def get_user_templates(
        self,
        user_id: str,
        rule_type: Optional[PreprocessingRuleType] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[DataPreprocessingRule]:
        """
        Get user's saved templates with optional type filter

        Args:
            user_id: User ID
            rule_type: Optional rule type filter
            skip: Number of records to skip
            limit: Maximum number of records to return (default 20)

        Returns:
            List of user's preprocessing templates

        Example:
            templates = await repo.get_user_templates(
                user_id="user-123",
                rule_type=PreprocessingRuleType.MISSING_VALUE
            )
        """
        query = select(self.model).where(
            self.model.user_id == user_id,
            self.model.is_template == True,
            self.model.is_deleted == False
        )

        if rule_type:
            query = query.where(self.model.rule_type == rule_type.value)

        query = query.order_by(
            self.model.usage_count.desc(),  # Most used first
            self.model.created_at.desc()
        ).offset(skip).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_user_templates(self, user_id: str) -> int:
        """
        Count user's saved templates (for quota enforcement)

        Args:
            user_id: User ID

        Returns:
            Number of templates owned by user

        Example:
            count = await repo.count_user_templates("user-123")
            if count >= 20:
                raise TemplateQuotaExceeded()
        """
        return await self.count(
            user_id=user_id,
            is_template=True
        )

    async def get_by_type(
        self,
        rule_type: PreprocessingRuleType,
        include_system: bool = True,
        user_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[DataPreprocessingRule]:
        """
        Get preprocessing rules by type

        Args:
            rule_type: Preprocessing rule type
            include_system: Whether to include system templates (user_id is NULL)
            user_id: Optional user ID to get user-specific rules
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of preprocessing rules

        Example:
            # Get all outlier detection templates (system + user's)
            rules = await repo.get_by_type(
                rule_type=PreprocessingRuleType.OUTLIER_DETECTION,
                user_id="user-123"
            )
        """
        query = select(self.model).where(
            self.model.rule_type == rule_type.value,
            self.model.is_deleted == False
        )

        # Build user filter conditions
        if user_id and include_system:
            # Get both user's templates and system templates
            query = query.where(
                (self.model.user_id == user_id) | (self.model.user_id == None)
            )
        elif user_id:
            # Only user's templates
            query = query.where(self.model.user_id == user_id)
        elif include_system:
            # Only system templates
            query = query.where(self.model.user_id == None)

        query = query.order_by(
            self.model.usage_count.desc(),
            self.model.created_at.desc()
        ).offset(skip).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_popular_templates(
        self,
        rule_type: Optional[PreprocessingRuleType] = None,
        limit: int = 10
    ) -> List[DataPreprocessingRule]:
        """
        Get most popular templates (highest usage_count)

        Args:
            rule_type: Optional rule type filter
            limit: Maximum number of records to return (default 10)

        Returns:
            List of popular templates

        Example:
            popular = await repo.get_popular_templates(limit=5)
        """
        query = select(self.model).where(
            self.model.is_template == True,
            self.model.is_deleted == False
        )

        if rule_type:
            query = query.where(self.model.rule_type == rule_type.value)

        query = query.order_by(
            self.model.usage_count.desc(),
            self.model.created_at.desc()
        ).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def increment_usage(self, rule_id: str) -> Optional[DataPreprocessingRule]:
        """
        Increment usage count for a template

        Args:
            rule_id: Rule ID

        Returns:
            Updated rule or None if not found

        Example:
            rule = await repo.increment_usage("rule-123")
        """
        rule = await self.get(rule_id)
        if rule:
            rule.usage_count += 1
            await self.session.flush()
            await self.session.refresh(rule)
        return rule

    async def search_templates(
        self,
        search_query: str,
        user_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[DataPreprocessingRule]:
        """
        Search templates by name or description

        Args:
            search_query: Search string
            user_id: Optional user ID to filter user templates
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of matching templates

        Example:
            templates = await repo.search_templates("outlier", user_id="user-123")
        """
        search_pattern = f"%{search_query}%"

        query = select(self.model).where(
            self.model.is_template == True,
            self.model.is_deleted == False,
            (
                self.model.name.ilike(search_pattern) |
                self.model.description.ilike(search_pattern)
            )
        )

        if user_id:
            query = query.where(
                (self.model.user_id == user_id) | (self.model.user_id == None)
            )

        query = query.order_by(
            self.model.usage_count.desc(),
            self.model.created_at.desc()
        ).offset(skip).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_user(
        self,
        user_id: str,
        rule_type: Optional[PreprocessingRuleType] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[DataPreprocessingRule]:
        """
        Get preprocessing rules by user ID with optional type filter

        Args:
            user_id: User ID
            rule_type: Optional rule type filter
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of preprocessing rules owned by the user

        Example:
            rules = await repo.get_by_user("user-123")
        """
        query = select(self.model).where(
            self.model.user_id == user_id,
            self.model.is_deleted == False
        )

        if rule_type:
            query = query.where(self.model.rule_type == rule_type.value)

        query = query.order_by(self.model.created_at.desc()).offset(skip).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_templates(
        self,
        rule_type: Optional[PreprocessingRuleType] = None,
        user_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[DataPreprocessingRule]:
        """
        Get all templates with optional filters

        Args:
            rule_type: Optional rule type filter
            user_id: Optional user ID filter (includes system templates if None)
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of preprocessing templates

        Example:
            templates = await repo.get_templates(
                rule_type=PreprocessingRuleType.OUTLIER_DETECTION
            )
        """
        query = select(self.model).where(
            self.model.is_template == True,
            self.model.is_deleted == False
        )

        if rule_type:
            query = query.where(self.model.rule_type == rule_type.value)

        if user_id:
            query = query.where(
                (self.model.user_id == user_id) | (self.model.user_id == None)
            )

        query = query.order_by(
            self.model.usage_count.desc(),
            self.model.created_at.desc()
        ).offset(skip).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_user_and_name(
        self,
        user_id: str,
        name: str
    ) -> Optional[DataPreprocessingRule]:
        """
        Get a rule by user ID and name (for duplicate checking)

        Args:
            user_id: User ID
            name: Rule name

        Returns:
            Rule if found, None otherwise

        Example:
            existing = await repo.get_by_user_and_name("user-123", "My Rule")
        """
        query = select(self.model).where(
            self.model.user_id == user_id,
            self.model.name == name,
            self.model.is_deleted == False
        )

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_with_filters(
        self,
        user_id: Optional[str] = None,
        rule_type: Optional[str] = None,
        is_template: Optional[bool] = None,
        search_term: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[DataPreprocessingRule]:
        """
        Get rules with multiple filters

        Args:
            user_id: Optional user ID filter
            rule_type: Optional rule type filter
            is_template: Optional template flag filter
            search_term: Optional search term for name/description
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of filtered rules

        Example:
            rules = await repo.get_with_filters(
                user_id="user-123",
                rule_type="missing_value",
                is_template=True
            )
        """
        query = select(self.model).where(self.model.is_deleted == False)

        if user_id:
            query = query.where(self.model.user_id == user_id)

        if rule_type:
            query = query.where(self.model.rule_type == rule_type)

        if is_template is not None:
            query = query.where(self.model.is_template == is_template)

        if search_term:
            search_pattern = f"%{search_term}%"
            query = query.where(
                (self.model.name.ilike(search_pattern)) |
                (self.model.description.ilike(search_pattern))
            )

        query = query.order_by(
            self.model.created_at.desc()
        ).offset(skip).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def increment_usage_count(self, rule_id: str) -> Optional[DataPreprocessingRule]:
        """
        Increment usage count for a rule/template

        Args:
            rule_id: Rule ID

        Returns:
            Updated rule or None if not found

        Example:
            rule = await repo.increment_usage_count("rule-123")
        """
        return await self.increment_usage(rule_id)


class PreprocessingTaskRepository(BaseRepository[DataPreprocessingTask]):
    """
    Repository for DataPreprocessingTask model with specialized query methods

    Handles:
    - Task execution tracking
    - Progress monitoring
    - Task history and statistics
    """

    def __init__(self, session: AsyncSession):
        super().__init__(DataPreprocessingTask, session)

    async def get_by_user(
        self,
        user_id: str,
        status: Optional[PreprocessingTaskStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[DataPreprocessingTask]:
        """
        Get preprocessing tasks by user ID with optional status filter

        Args:
            user_id: User ID
            status: Optional status filter
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of preprocessing tasks

        Example:
            tasks = await repo.get_by_user(
                user_id="user-123",
                status=PreprocessingTaskStatus.RUNNING
            )
        """
        query = select(self.model).where(
            self.model.user_id == user_id,
            self.model.is_deleted == False
        )

        if status:
            query = query.where(self.model.status == status.value)

        query = query.order_by(self.model.created_at.desc()).offset(skip).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_active_tasks(
        self,
        user_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[DataPreprocessingTask]:
        """
        Get all active (pending/running) preprocessing tasks

        Args:
            user_id: Optional user ID filter
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of active preprocessing tasks

        Example:
            active = await repo.get_active_tasks()
        """
        active_statuses = [
            PreprocessingTaskStatus.PENDING.value,
            PreprocessingTaskStatus.RUNNING.value,
        ]

        query = select(self.model).where(
            self.model.status.in_(active_statuses),
            self.model.is_deleted == False
        )

        if user_id:
            query = query.where(self.model.user_id == user_id)

        query = query.order_by(self.model.created_at.desc()).offset(skip).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_status(
        self,
        status: PreprocessingTaskStatus,
        skip: int = 0,
        limit: int = 100
    ) -> List[DataPreprocessingTask]:
        """
        Get preprocessing tasks by status

        Args:
            status: Task status
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of tasks with specified status

        Example:
            failed = await repo.get_by_status(PreprocessingTaskStatus.FAILED)
        """
        query = select(self.model).where(
            self.model.status == status.value,
            self.model.is_deleted == False
        ).order_by(self.model.created_at.desc()).offset(skip).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_dataset(
        self,
        dataset_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[DataPreprocessingTask]:
        """
        Get preprocessing tasks for a specific dataset

        Args:
            dataset_id: Dataset ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of preprocessing tasks for the dataset

        Example:
            tasks = await repo.get_by_dataset("dataset-123")
        """
        query = select(self.model).where(
            self.model.dataset_id == dataset_id,
            self.model.is_deleted == False
        ).order_by(self.model.created_at.desc()).offset(skip).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_rule(
        self,
        rule_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[DataPreprocessingTask]:
        """
        Get preprocessing tasks that used a specific rule/template

        Args:
            rule_id: Rule ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of preprocessing tasks using the rule

        Example:
            tasks = await repo.get_by_rule("rule-123")
        """
        query = select(self.model).where(
            self.model.rule_id == rule_id,
            self.model.is_deleted == False
        ).order_by(self.model.created_at.desc()).offset(skip).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_by_status(self, status: PreprocessingTaskStatus) -> int:
        """
        Count preprocessing tasks by status

        Args:
            status: Task status

        Returns:
            Count of tasks with specified status

        Example:
            pending = await repo.count_by_status(PreprocessingTaskStatus.PENDING)
        """
        return await self.count(status=status.value)

    async def get_task_statistics(self, user_id: Optional[str] = None) -> dict:
        """
        Get task execution statistics

        Args:
            user_id: Optional user ID to filter statistics

        Returns:
            Dictionary with task statistics

        Example:
            stats = await repo.get_task_statistics(user_id="user-123")
            # Returns: {
            #     "total": 100,
            #     "completed": 85,
            #     "failed": 10,
            #     "running": 5,
            #     "average_execution_time": 45.2
            # }
        """
        query = select(
            func.count(self.model.id).label("total"),
            func.count(
                self.model.id
            ).filter(
                self.model.status == PreprocessingTaskStatus.COMPLETED.value
            ).label("completed"),
            func.count(
                self.model.id
            ).filter(
                self.model.status == PreprocessingTaskStatus.FAILED.value
            ).label("failed"),
            func.count(
                self.model.id
            ).filter(
                self.model.status == PreprocessingTaskStatus.RUNNING.value
            ).label("running"),
            func.avg(self.model.execution_time_seconds).label("avg_execution_time")
        ).where(self.model.is_deleted == False)

        if user_id:
            query = query.where(self.model.user_id == user_id)

        result = await self.session.execute(query)
        row = result.first()

        return {
            "total": row.total or 0,
            "completed": row.completed or 0,
            "failed": row.failed or 0,
            "running": row.running or 0,
            "average_execution_time": float(row.avg_execution_time) if row.avg_execution_time else 0.0
        }
