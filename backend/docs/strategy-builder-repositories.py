"""
Strategy Builder Repository Layer Interface Definitions

This module defines repository classes for Strategy Builder data access.
All repositories extend BaseRepository and provide specialized query methods.

Pattern:
- Inherit from BaseRepository[ModelType]
- Add model-specific query methods
- Follow async/await patterns
- Use SQLAlchemy 2.0 select() syntax
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.base import BaseRepository
from app.database.models.strategy_builder import (
    NodeTemplate,
    QuickTest,
    CodeGeneration,
    BuilderSession,
    NodeTypeCategory,
    QuickTestStatus,
    ValidationStatus,
    SessionType
)


class NodeTemplateRepository(BaseRepository[NodeTemplate]):
    """
    Repository for NodeTemplate model.

    Provides specialized queries for:
    - Filtering by node type and category
    - System vs custom template queries
    - User-specific template queries
    - Usage statistics tracking
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with NodeTemplate model."""
        super().__init__(NodeTemplate, session)

    async def get_by_name_and_user(
        self,
        name: str,
        user_id: Optional[str] = None,
        is_system_template: bool = False
    ) -> Optional[NodeTemplate]:
        """
        Get template by name and user (for uniqueness check).

        Args:
            name: Template name
            user_id: User ID (for custom templates)
            is_system_template: Whether to search system templates

        Returns:
            NodeTemplate if found, None otherwise
        """
        stmt = select(self.model).where(
            and_(
                self.model.name == name,
                self.model.is_system_template == is_system_template,
                self.model.is_deleted == False
            )
        )

        if not is_system_template and user_id:
            stmt = stmt.where(self.model.user_id == user_id)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_filters(
        self,
        node_type: Optional[NodeTypeCategory] = None,
        category: Optional[str] = None,
        is_system_template: Optional[bool] = None,
        user_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[NodeTemplate]:
        """
        Get templates with multiple filters.

        Args:
            node_type: Filter by node type
            category: Filter by category
            is_system_template: Filter by system/custom
            user_id: Include user's custom templates
            skip: Pagination offset
            limit: Max records

        Returns:
            List of NodeTemplate instances
        """
        stmt = select(self.model).where(self.model.is_deleted == False)

        # Apply filters
        if node_type is not None:
            stmt = stmt.where(self.model.node_type == node_type.value)

        if category is not None:
            stmt = stmt.where(self.model.category == category)

        if is_system_template is not None:
            stmt = stmt.where(self.model.is_system_template == is_system_template)
        elif user_id:
            # Include both system templates and user's custom templates
            stmt = stmt.where(
                or_(
                    self.model.is_system_template == True,
                    and_(
                        self.model.is_system_template == False,
                        self.model.user_id == user_id
                    )
                )
            )

        # Order by usage count (popular first), then name
        stmt = stmt.order_by(
            desc(self.model.usage_count),
            self.model.name
        )

        # Pagination
        stmt = stmt.offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_filters(
        self,
        node_type: Optional[NodeTypeCategory] = None,
        category: Optional[str] = None,
        is_system_template: Optional[bool] = None,
        user_id: Optional[str] = None
    ) -> int:
        """
        Count templates matching filters.

        Args:
            node_type: Filter by node type
            category: Filter by category
            is_system_template: Filter by system/custom
            user_id: Include user's custom templates

        Returns:
            Total count
        """
        stmt = select(func.count()).select_from(self.model).where(
            self.model.is_deleted == False
        )

        # Apply same filters as get_by_filters
        if node_type is not None:
            stmt = stmt.where(self.model.node_type == node_type.value)

        if category is not None:
            stmt = stmt.where(self.model.category == category)

        if is_system_template is not None:
            stmt = stmt.where(self.model.is_system_template == is_system_template)
        elif user_id:
            stmt = stmt.where(
                or_(
                    self.model.is_system_template == True,
                    and_(
                        self.model.is_system_template == False,
                        self.model.user_id == user_id
                    )
                )
            )

        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_system_templates(
        self,
        node_type: Optional[NodeTypeCategory] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[NodeTemplate]:
        """
        Get all system templates.

        Args:
            node_type: Optional filter by node type
            skip: Pagination offset
            limit: Max records

        Returns:
            List of system NodeTemplate instances
        """
        return await self.get_by_filters(
            node_type=node_type,
            is_system_template=True,
            skip=skip,
            limit=limit
        )

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
            skip: Pagination offset
            limit: Max records

        Returns:
            List of custom NodeTemplate instances
        """
        stmt = select(self.model).where(
            and_(
                self.model.user_id == user_id,
                self.model.is_system_template == False,
                self.model.is_deleted == False
            )
        )

        if node_type is not None:
            stmt = stmt.where(self.model.node_type == node_type.value)

        stmt = stmt.order_by(desc(self.model.created_at))
        stmt = stmt.offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def increment_usage_count(
        self,
        template_id: str
    ) -> Optional[NodeTemplate]:
        """
        Increment usage count for template.

        Args:
            template_id: Template ID

        Returns:
            Updated NodeTemplate instance
        """
        template = await self.get(template_id)
        if template:
            template.usage_count += 1
            await self.session.flush()
            await self.session.refresh(template)
        return template

    async def get_popular_templates(
        self,
        limit: int = 10
    ) -> List[NodeTemplate]:
        """
        Get most popular templates by usage count.

        Args:
            limit: Number of templates to return

        Returns:
            List of popular NodeTemplate instances
        """
        stmt = select(self.model).where(
            self.model.is_deleted == False
        ).order_by(
            desc(self.model.usage_count)
        ).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class QuickTestRepository(BaseRepository[QuickTest]):
    """
    Repository for QuickTest model.

    Provides specialized queries for:
    - User's test history
    - Instance-specific tests
    - Status-based filtering
    - Active/pending tests
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with QuickTest model."""
        super().__init__(QuickTest, session)

    async def get_by_instance_and_user(
        self,
        instance_id: str,
        user_id: str,
        status: Optional[QuickTestStatus] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[QuickTest]:
        """
        Get quick tests for specific instance and user.

        Args:
            instance_id: Strategy instance ID
            user_id: User ID
            status: Optional status filter
            skip: Pagination offset
            limit: Max records

        Returns:
            List of QuickTest instances
        """
        stmt = select(self.model).where(
            and_(
                self.model.instance_id == instance_id,
                self.model.user_id == user_id,
                self.model.is_deleted == False
            )
        )

        if status is not None:
            stmt = stmt.where(self.model.status == status.value)

        stmt = stmt.order_by(desc(self.model.created_at))
        stmt = stmt.offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_user(
        self,
        user_id: str,
        status: Optional[QuickTestStatus] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[QuickTest]:
        """
        Get all quick tests for user.

        Args:
            user_id: User ID
            status: Optional status filter
            skip: Pagination offset
            limit: Max records

        Returns:
            List of QuickTest instances
        """
        stmt = select(self.model).where(
            and_(
                self.model.user_id == user_id,
                self.model.is_deleted == False
            )
        )

        if status is not None:
            stmt = stmt.where(self.model.status == status.value)

        stmt = stmt.order_by(desc(self.model.created_at))
        stmt = stmt.offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_instance_and_user(
        self,
        instance_id: str,
        user_id: str,
        status: Optional[QuickTestStatus] = None
    ) -> int:
        """Count quick tests for instance and user."""
        stmt = select(func.count()).select_from(self.model).where(
            and_(
                self.model.instance_id == instance_id,
                self.model.user_id == user_id,
                self.model.is_deleted == False
            )
        )

        if status is not None:
            stmt = stmt.where(self.model.status == status.value)

        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def count_by_user(
        self,
        user_id: str,
        status: Optional[QuickTestStatus] = None
    ) -> int:
        """Count quick tests for user."""
        stmt = select(func.count()).select_from(self.model).where(
            and_(
                self.model.user_id == user_id,
                self.model.is_deleted == False
            )
        )

        if status is not None:
            stmt = stmt.where(self.model.status == status.value)

        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_pending_tests(
        self,
        limit: int = 100
    ) -> List[QuickTest]:
        """
        Get pending quick tests (for background worker).

        Args:
            limit: Max records to fetch

        Returns:
            List of QuickTest instances with PENDING status
        """
        stmt = select(self.model).where(
            and_(
                self.model.status == QuickTestStatus.PENDING.value,
                self.model.is_deleted == False
            )
        ).order_by(
            self.model.created_at
        ).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_running_tests(
        self,
        timeout_minutes: int = 30
    ) -> List[QuickTest]:
        """
        Get running tests that may have timed out.

        Args:
            timeout_minutes: Consider tests running longer than this as timed out

        Returns:
            List of QuickTest instances that may have timed out
        """
        timeout_threshold = datetime.now() - timedelta(minutes=timeout_minutes)

        stmt = select(self.model).where(
            and_(
                self.model.status == QuickTestStatus.RUNNING.value,
                self.model.started_at < timeout_threshold,
                self.model.is_deleted == False
            )
        )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(
        self,
        test_id: str,
        status: QuickTestStatus,
        error_message: Optional[str] = None
    ) -> Optional[QuickTest]:
        """
        Update test status.

        Args:
            test_id: Test ID
            status: New status
            error_message: Optional error message

        Returns:
            Updated QuickTest instance
        """
        update_data = {"status": status.value}

        if status == QuickTestStatus.RUNNING:
            update_data["started_at"] = datetime.now()
        elif status in [QuickTestStatus.COMPLETED, QuickTestStatus.FAILED, QuickTestStatus.CANCELLED]:
            update_data["completed_at"] = datetime.now()

        if error_message:
            update_data["error_message"] = error_message

        return await self.update(test_id, update_data)


class CodeGenerationRepository(BaseRepository[CodeGeneration]):
    """
    Repository for CodeGeneration model.

    Provides specialized queries for:
    - Code generation history
    - Code hash-based deduplication
    - Validation status filtering
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with CodeGeneration model."""
        super().__init__(CodeGeneration, session)

    async def get_by_instance(
        self,
        instance_id: str,
        skip: int = 0,
        limit: int = 10
    ) -> List[CodeGeneration]:
        """
        Get code generation history for instance.

        Args:
            instance_id: Strategy instance ID
            skip: Pagination offset
            limit: Max records

        Returns:
            List of CodeGeneration instances ordered by creation time (newest first)
        """
        stmt = select(self.model).where(
            and_(
                self.model.instance_id == instance_id,
                self.model.is_deleted == False
            )
        ).order_by(
            desc(self.model.created_at)
        ).offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_instance(
        self,
        instance_id: str
    ) -> int:
        """Count code generations for instance."""
        stmt = select(func.count()).select_from(self.model).where(
            and_(
                self.model.instance_id == instance_id,
                self.model.is_deleted == False
            )
        )

        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_by_code_hash(
        self,
        instance_id: str,
        code_hash: str
    ) -> Optional[CodeGeneration]:
        """
        Get code generation by hash (for deduplication).

        Args:
            instance_id: Strategy instance ID
            code_hash: SHA-256 hash of code

        Returns:
            CodeGeneration instance if found, None otherwise
        """
        stmt = select(self.model).where(
            and_(
                self.model.instance_id == instance_id,
                self.model.code_hash == code_hash,
                self.model.is_deleted == False
            )
        ).order_by(
            desc(self.model.created_at)
        ).limit(1)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_validation_status(
        self,
        validation_status: ValidationStatus,
        skip: int = 0,
        limit: int = 100
    ) -> List[CodeGeneration]:
        """
        Get code generations by validation status.

        Args:
            validation_status: Validation status filter
            skip: Pagination offset
            limit: Max records

        Returns:
            List of CodeGeneration instances
        """
        stmt = select(self.model).where(
            and_(
                self.model.validation_status == validation_status.value,
                self.model.is_deleted == False
            )
        ).order_by(
            desc(self.model.created_at)
        ).offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_latest_valid_code(
        self,
        instance_id: str
    ) -> Optional[CodeGeneration]:
        """
        Get latest valid code generation for instance.

        Args:
            instance_id: Strategy instance ID

        Returns:
            Latest CodeGeneration with VALID status, None if not found
        """
        stmt = select(self.model).where(
            and_(
                self.model.instance_id == instance_id,
                self.model.validation_status == ValidationStatus.VALID.value,
                self.model.syntax_check_passed == True,
                self.model.security_check_passed == True,
                self.model.is_deleted == False
            )
        ).order_by(
            desc(self.model.created_at)
        ).limit(1)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_user(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 20
    ) -> List[CodeGeneration]:
        """
        Get code generations by user.

        Args:
            user_id: User ID
            skip: Pagination offset
            limit: Max records

        Returns:
            List of CodeGeneration instances
        """
        stmt = select(self.model).where(
            and_(
                self.model.user_id == user_id,
                self.model.is_deleted == False
            )
        ).order_by(
            desc(self.model.created_at)
        ).offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class BuilderSessionRepository(BaseRepository[BuilderSession]):
    """
    Repository for BuilderSession model.

    Provides specialized queries for:
    - Active session retrieval
    - Expired session cleanup
    - User session management
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with BuilderSession model."""
        super().__init__(BuilderSession, session)

    async def get_active_by_instance_and_user(
        self,
        instance_id: str,
        user_id: str
    ) -> Optional[BuilderSession]:
        """
        Get active session for instance and user.

        Args:
            instance_id: Strategy instance ID
            user_id: User ID

        Returns:
            Active BuilderSession if found, None otherwise
        """
        stmt = select(self.model).where(
            and_(
                self.model.instance_id == instance_id,
                self.model.user_id == user_id,
                self.model.is_active == True,
                self.model.is_deleted == False
            )
        ).order_by(
            desc(self.model.last_activity_at)
        ).limit(1)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_by_user(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 10
    ) -> List[BuilderSession]:
        """
        Get all active sessions for user.

        Args:
            user_id: User ID
            skip: Pagination offset
            limit: Max records

        Returns:
            List of active BuilderSession instances
        """
        stmt = select(self.model).where(
            and_(
                self.model.user_id == user_id,
                self.model.is_active == True,
                self.model.is_deleted == False
            )
        ).order_by(
            desc(self.model.last_activity_at)
        ).offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_expired_sessions(
        self,
        expiration_hours: int = 24
    ) -> List[BuilderSession]:
        """
        Get expired sessions for cleanup.

        Args:
            expiration_hours: Hours of inactivity before expiration

        Returns:
            List of expired BuilderSession instances
        """
        expiration_threshold = datetime.now() - timedelta(hours=expiration_hours)

        stmt = select(self.model).where(
            and_(
                self.model.is_active == True,
                self.model.last_activity_at < expiration_threshold,
                self.model.is_deleted == False
            )
        )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_activity(
        self,
        session_id: str,
        draft_logic_flow: Dict[str, Any],
        draft_parameters: Dict[str, Any],
        draft_metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[BuilderSession]:
        """
        Update session activity (auto-save).

        Args:
            session_id: Session ID
            draft_logic_flow: Updated logic flow
            draft_parameters: Updated parameters
            draft_metadata: Optional UI metadata

        Returns:
            Updated BuilderSession instance
        """
        update_data = {
            "draft_logic_flow": draft_logic_flow,
            "draft_parameters": draft_parameters,
            "last_activity_at": datetime.now()
        }

        if draft_metadata is not None:
            update_data["draft_metadata"] = draft_metadata

        return await self.update(session_id, update_data)

    async def deactivate_session(
        self,
        session_id: str
    ) -> Optional[BuilderSession]:
        """
        Deactivate session (when strategy is saved or discarded).

        Args:
            session_id: Session ID

        Returns:
            Updated BuilderSession instance
        """
        return await self.update(session_id, {"is_active": False})

    async def create_or_update_by_instance(
        self,
        instance_id: Optional[str],
        user_id: str,
        draft_logic_flow: Dict[str, Any],
        draft_parameters: Dict[str, Any],
        session_name: Optional[str] = None,
        session_type: SessionType = SessionType.AUTOSAVE,
        draft_metadata: Optional[Dict[str, Any]] = None
    ) -> BuilderSession:
        """
        Create or update session (upsert).

        Args:
            instance_id: Strategy instance ID (None for new strategies)
            user_id: User ID
            draft_logic_flow: Draft logic flow
            draft_parameters: Draft parameters
            session_name: Optional session name
            session_type: Session type
            draft_metadata: Optional UI metadata

        Returns:
            Created or updated BuilderSession instance
        """
        # Try to find existing active session
        existing_session = None
        if instance_id:
            existing_session = await self.get_active_by_instance_and_user(
                instance_id, user_id
            )

        if existing_session:
            # Update existing session
            return await self.update_activity(
                existing_session.id,
                draft_logic_flow,
                draft_parameters,
                draft_metadata
            )
        else:
            # Create new session
            session_data = {
                "instance_id": instance_id,
                "user_id": user_id,
                "session_name": session_name,
                "session_type": session_type.value,
                "draft_logic_flow": draft_logic_flow,
                "draft_parameters": draft_parameters,
                "draft_metadata": draft_metadata,
                "is_active": True,
                "last_activity_at": datetime.now(),
                "expires_at": datetime.now() + timedelta(hours=24)
            }
            return await self.create(session_data, user_id=user_id)


# ==================== Type Exports ====================

__all__ = [
    "NodeTemplateRepository",
    "QuickTestRepository",
    "CodeGenerationRepository",
    "BuilderSessionRepository"
]
