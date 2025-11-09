"""
CodeGeneration Repository

Repository for managing code generation operations with specialized
query methods for version tracking and deduplication.
"""

from typing import List, Optional

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.strategy_builder import CodeGeneration, ValidationStatus as CodeValidationStatus
from app.database.repositories.base import BaseRepository


class CodeGenerationRepository(BaseRepository[CodeGeneration]):
    """
    Repository for CodeGeneration operations.

    Provides specialized methods for:
    - Code hash-based deduplication
    - Instance generation history tracking
    - Validation status management
    - Latest version retrieval
    - User code generation queries
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with CodeGeneration model"""
        super().__init__(CodeGeneration, session)

    async def find_by_code_hash(
        self,
        code_hash: str,
        instance_id: Optional[str] = None
    ) -> List[CodeGeneration]:
        """
        Find code generations by code hash for deduplication.

        Args:
            code_hash: SHA-256 hash of generated code
            instance_id: Optional filter by instance ID

        Returns:
            List of code generations with matching hash
        """
        stmt = select(CodeGeneration).where(
            CodeGeneration.code_hash == code_hash,
            CodeGeneration.is_deleted == False
        )

        if instance_id:
            stmt = stmt.where(CodeGeneration.instance_id == instance_id)

        stmt = stmt.order_by(CodeGeneration.created_at.desc())

        result = await self.session.execute(stmt)
        generations = list(result.scalars().all())

        logger.debug(f"Found {len(generations)} generations with hash {code_hash[:8]}...")
        return generations

    async def find_history_by_instance(
        self,
        instance_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[CodeGeneration]:
        """
        Get code generation history for a strategy instance.

        Args:
            instance_id: Strategy instance ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of code generations ordered by creation time (newest first)
        """
        stmt = select(CodeGeneration).where(
            CodeGeneration.instance_id == instance_id,
            CodeGeneration.is_deleted == False
        )

        # Order by created_at descending (newest first)
        stmt = stmt.order_by(CodeGeneration.created_at.desc())
        stmt = stmt.offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        generations = list(result.scalars().all())

        logger.debug(f"Found {len(generations)} generations for instance {instance_id}")
        return generations

    async def get_latest_by_instance(
        self,
        instance_id: str
    ) -> Optional[CodeGeneration]:
        """
        Get the latest code generation for an instance.

        Args:
            instance_id: Strategy instance ID

        Returns:
            Latest code generation or None if no generations exist
        """
        stmt = select(CodeGeneration).where(
            CodeGeneration.instance_id == instance_id,
            CodeGeneration.is_deleted == False
        )

        stmt = stmt.order_by(CodeGeneration.created_at.desc())
        stmt = stmt.limit(1)

        result = await self.session.execute(stmt)
        generation = result.scalar_one_or_none()

        if generation:
            logger.debug(f"Retrieved latest generation for instance {instance_id}")
        else:
            logger.debug(f"No generations found for instance {instance_id}")

        return generation

    async def update_validation_status(
        self,
        generation_id: str,
        status: CodeValidationStatus,
        validation_result: Optional[dict] = None,
        syntax_check_passed: Optional[bool] = None,
        security_check_passed: Optional[bool] = None,
        commit: bool = True
    ) -> Optional[CodeGeneration]:
        """
        Update validation status and results for a code generation.

        Args:
            generation_id: Code generation ID
            status: New validation status
            validation_result: Detailed validation results
            syntax_check_passed: Whether syntax check passed
            security_check_passed: Whether security check passed
            commit: Whether to commit the transaction

        Returns:
            Updated code generation or None if not found
        """
        generation = await self.get(generation_id)
        if not generation:
            logger.warning(f"Code generation not found: {generation_id}")
            return None

        # Update validation fields
        update_data = {
            "validation_status": status.value
        }

        if validation_result is not None:
            update_data["validation_result"] = validation_result

        if syntax_check_passed is not None:
            update_data["syntax_check_passed"] = syntax_check_passed

        if security_check_passed is not None:
            update_data["security_check_passed"] = security_check_passed

        # Use base update method
        updated = await self.update(generation_id, update_data, commit=commit)

        logger.debug(
            f"Updated validation status for generation {generation_id} to {status.value}"
        )
        return updated

    async def find_by_user(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[CodeGeneration]:
        """
        Get all code generations by a user.

        Args:
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of user's code generations
        """
        stmt = select(CodeGeneration).where(
            CodeGeneration.user_id == user_id,
            CodeGeneration.is_deleted == False
        )

        stmt = stmt.order_by(CodeGeneration.created_at.desc())
        stmt = stmt.offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        generations = list(result.scalars().all())

        logger.debug(f"Found {len(generations)} generations for user {user_id}")
        return generations

    async def find_by_validation_status(
        self,
        status: CodeValidationStatus,
        skip: int = 0,
        limit: int = 100
    ) -> List[CodeGeneration]:
        """
        Get code generations by validation status.

        Args:
            status: Validation status to filter by
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of code generations with the specified status
        """
        stmt = select(CodeGeneration).where(
            CodeGeneration.validation_status == status.value,
            CodeGeneration.is_deleted == False
        )

        stmt = stmt.order_by(CodeGeneration.created_at.desc())
        stmt = stmt.offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        generations = list(result.scalars().all())

        logger.debug(f"Found {len(generations)} generations with status {status.value}")
        return generations
